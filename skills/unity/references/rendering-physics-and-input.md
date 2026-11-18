# Rendering, physics and input

URP configuration, render graph passes, shaders and materials, physics settings and queries,
movement models, and the Input System.

## Contents

- URP project settings
- Custom passes with the render graph
- Shaders
- Materials at runtime
- Physics settings and layers
- Physics queries
- Movement: Rigidbody, kinematic, CharacterController
- Input System setup
- Reading input
- Rebinding
- UI input
- Cameras

## URP project settings

| Setting | Value | Why |
|---|---|---|
| URP Asset per quality tier | One asset per tier (for example `URP-High`, `URP-Mobile`) in `Settings/`, assigned in Quality settings | Per-platform cost control without code |
| Rendering Path (Universal Renderer) | Forward+ | No per-object light limit; required by the GPU Resident Drawer |
| SRP Batcher | On | Fewer state changes; requires compatible shaders |
| Render Graph Compatibility Mode | Off | Compatibility Mode is deprecated; new passes use `RecordRenderGraph` |
| GPU Resident Drawer | On for scenes with many static or repeated `MeshRenderer`s | Instanced drawing without code; needs Forward+ and BatchRendererGroup Variants set to Keep All |
| Upscaling | STP where the target supports compute | Render at lower resolution with temporal reconstruction |
| Depth Texture, Opaque Texture | Off unless a shader samples them | Each costs a full-screen copy |
| Post-processing | One global Volume with a shared profile; local Volumes for areas | Never instantiate profiles per frame |

Lighting choices (baked, Adaptive Probe Volumes, realtime) are per project; record them in the
project's `AGENTS.md` so every session follows the same one.

## Custom passes with the render graph

Prefer the built-in Full Screen Pass Renderer Feature with a Fullscreen Shader Graph for
full-screen effects: no code. Write a pass only when that cannot express the effect.

```csharp
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.Universal;

public sealed class TintFeature : ScriptableRendererFeature
{
    [SerializeField] Material material;
    [SerializeField] RenderPassEvent passEvent = RenderPassEvent.BeforeRenderingPostProcessing;
    TintPass _pass;

    public override void Create() => _pass = new TintPass { renderPassEvent = passEvent };

    public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
    {
        if (material == null) return;
        _pass.Setup(material);
        renderer.EnqueuePass(_pass);
    }

    sealed class TintPass : ScriptableRenderPass
    {
        Material _material;

        sealed class PassData
        {
            public TextureHandle Source;
            public Material Material;
        }

        public void Setup(Material material) => _material = material;

        public override void RecordRenderGraph(RenderGraph renderGraph, ContextContainer frameData)
        {
            var cameraData = frameData.Get<UniversalCameraData>();
            if (cameraData.cameraType == CameraType.Preview) return;

            var resources = frameData.Get<UniversalResourceData>();
            if (resources.isActiveTargetBackBuffer) return; // the back buffer cannot be sampled

            RenderTextureDescriptor desc = cameraData.cameraTargetDescriptor;
            desc.depthBufferBits = 0;
            TextureHandle destination =
                UniversalRenderer.CreateRenderGraphTexture(renderGraph, desc, "_TintTarget", false);

            using (var builder = renderGraph.AddRasterRenderPass<PassData>("Tint", out var data))
            {
                data.Source = resources.activeColorTexture;
                data.Material = _material;
                builder.UseTexture(data.Source);
                builder.SetRenderAttachment(destination, 0);
                builder.SetRenderFunc(static (PassData d, RasterGraphContext ctx) =>
                    Blitter.BlitTexture(ctx.cmd, d.Source, new Vector4(1f, 1f, 0f, 0f), d.Material, 0));
            }

            resources.cameraColor = destination; // later passes read the tinted image
        }
    }
}
```

- The render function is a `static` lambda: it captures nothing and allocates nothing per frame.
  Everything it needs travels in `PassData`.
- The blit material samples `_BlitTexture`: a Fullscreen Shader Graph, or a hand-written shader
  that includes `Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl` and uses its
  `Vert` function.
- Inspect passes and resource lifetimes in the Render Graph Viewer before guessing at a bug.
- `SetupRenderPasses` is deprecated; configure inputs in `AddRenderPasses`.

## Shaders

Prefer Shader Graph (URP Lit, Unlit, Fullscreen targets): it stays compatible with the SRP Batcher,
the depth prepass, and the GPU Resident Drawer across upgrades. A hand-written shader needs at
least this shape to batch:

```hlsl
Shader "Game/UnlitTint"
{
    Properties
    {
        _BaseMap ("Base Map", 2D) = "white" {}
        _BaseColor ("Base Color", Color) = (1, 1, 1, 1)
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }
        Pass
        {
            Name "Forward"
            Tags { "LightMode" = "UniversalForward" }

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_BaseMap);
            SAMPLER(sampler_BaseMap);

            CBUFFER_START(UnityPerMaterial)   // every material property, nothing else
                float4 _BaseMap_ST;
                half4 _BaseColor;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; };
            struct Varyings { float4 positionHCS : SV_POSITION; float2 uv : TEXCOORD0; };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                output.positionHCS = TransformObjectToHClip(input.positionOS.xyz);
                output.uv = TRANSFORM_TEX(input.uv, _BaseMap);
                return output;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                return SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv) * _BaseColor;
            }
            ENDHLSL
        }
    }
}
```

- Every property declared in `Properties` is in the `UnityPerMaterial` buffer, with the same set
  in every pass, or the shader is not SRP Batcher compatible. The shader inspector says which.
- Without `DepthOnly` and `DepthNormals` passes the object is missing from the depth prepass,
  SSAO and some post effects; without `ShadowCaster` it casts no shadow.
- Hand-written shaders need DOTS instancing support to be drawn by the GPU Resident Drawer; Shader
  Graph and URP Lit have it.
- Material toggles use `#pragma shader_feature_local` (unused variants are stripped). Use
  `multi_compile_local` only for keywords toggled at runtime, and set them through a cached
  `LocalKeyword` with `material.SetKeyword(keyword, enabled)`.
- Property IDs are `static readonly int` fields from `Shader.PropertyToID`.

## Materials at runtime

| Need | Use | Cost |
|---|---|---|
| Same look on many renderers | `sharedMaterial` | None |
| A tweak on a few objects | `renderer.material` (creates an instance) and `Destroy` it in `OnDestroy` | One material per object; leaks if not destroyed |
| Per-object colour on many objects | A small set of material variants, or per-instance data in the shader | `MaterialPropertyBlock` removes the renderer from the SRP Batcher and the GPU Resident Drawer |
| Animated global value (time of day, damage flash on all) | `Shader.SetGlobalFloat(id, v)` | One call per frame |

## Physics settings and layers

- Define layers in Tags and Layers (`ProjectSettings/TagManager.asset`): for example `Player`,
  `Enemy`, `Projectile`, `Environment`, `Interactable`. Never hard-code layer numbers; serialize a
  `LayerMask`, or resolve `LayerMask.NameToLayer` once in `Awake`.
- Layer Collision Matrix (Project Settings > Physics): disable every pair that never needs
  contacts (`Projectile`/`Projectile`, `Interactable`/`Environment`). It is the cheapest
  optimisation in physics.
- Queries Hit Triggers: off. Opt in per query with `QueryTriggerInteraction.Collide`.
- Auto Sync Transforms: off. Reuse Collision Callbacks: on, and never store the `Collision`
  object passed to a callback.
- Player-visible `Rigidbody`: Interpolate. Fast movers: Continuous Dynamic or Continuous
  Speculative. Everything else: Discrete.
- Simulation mode: Fixed Update for the game; Script (`Physics.simulationMode =
  SimulationMode.Script`, then `Physics.Simulate(Time.fixedDeltaTime)`) for tests, replays and
  rollback.
- 2D physics: use the `Physics2D` query overloads that take a `ContactFilter2D` and a `List<T>` or
  array; the 2D `NonAlloc` variants are deprecated.

## Physics queries

```csharp
using UnityEngine;

public sealed class Sensor : MonoBehaviour
{
    [SerializeField] LayerMask hitMask;
    [SerializeField, Min(0f)] float radius = 0.3f;
    [SerializeField, Min(0f)] float range = 20f;
    readonly RaycastHit[] _hits = new RaycastHit[16];

    public bool TryNearestHit(Vector3 origin, Vector3 direction, out RaycastHit nearest)
    {
        int count = Physics.SphereCastNonAlloc(origin, radius, direction, _hits, range, hitMask,
            QueryTriggerInteraction.Ignore);
        nearest = default;
        if (count == 0) return false;
        if (count == _hits.Length) Debug.LogWarning("Sensor buffer full; hits were dropped", this);

        int best = 0; // NonAlloc results are unsorted
        for (int i = 1; i < count; i++)
            if (_hits[i].distance < _hits[best].distance) best = i;
        nearest = _hits[best];
        return true;
    }
}
```

- `Physics.Raycast(..., out RaycastHit hit, ...)` for the single nearest hit allocates nothing.
- `Physics.CheckSphere` / `CheckCapsule` answer "is anything there" without results.
- Hundreds of rays per frame: `RaycastCommand.ScheduleBatch` with `NativeArray` buffers allocated
  once (`Allocator.Persistent`) and disposed in `OnDestroy`.
- Collision callbacks: `collision.GetContacts(buffer)` instead of `collision.contacts`.

## Movement: Rigidbody, kinematic, CharacterController

| Body | Use for | Move with | Step |
|---|---|---|---|
| Dynamic `Rigidbody` | Physics-driven characters, vehicles, props | `AddForce`, `linearVelocity` | `FixedUpdate` |
| Kinematic `Rigidbody` | Platforms, doors, scripted movers that push dynamic bodies | `MovePosition`, `MoveRotation` | `FixedUpdate` |
| `CharacterController` | Tight platformer or FPS control without forces | `Move` once per step; own gravity, slopes, step offset | One fixed choice per project (see below) |

Dynamic body with acceleration-limited control and a latched jump:

```csharp
using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(Rigidbody))]
public sealed class RigidbodyMover : MonoBehaviour
{
    [SerializeField] InputActionReference move;
    [SerializeField] InputActionReference jump;
    [SerializeField] LayerMask groundMask;
    [SerializeField, Min(0f)] float maxSpeed = 6f;
    [SerializeField, Min(0f)] float acceleration = 40f;
    [SerializeField, Min(0f)] float jumpSpeed = 6f;

    Rigidbody _body;
    Vector2 _move;
    bool _jumpLatched;

    void Awake() => _body = GetComponent<Rigidbody>();

    void Update()
    {
        _move = move.action.ReadValue<Vector2>();
        if (jump.action.WasPressedThisFrame()) _jumpLatched = true;
    }

    void FixedUpdate()
    {
        Vector3 v = _body.linearVelocity;
        Vector3 target = new Vector3(_move.x, 0f, _move.y) * maxSpeed;
        Vector3 delta = Vector3.ClampMagnitude(target - new Vector3(v.x, 0f, v.z),
            acceleration * Time.fixedDeltaTime);
        _body.AddForce(delta, ForceMode.VelocityChange);

        // Probe below a height-2 capsule with its pivot at the centre
        bool grounded = Physics.CheckSphere(_body.position + Vector3.down * 0.9f, 0.2f, groundMask,
            QueryTriggerInteraction.Ignore);
        if (_jumpLatched && grounded)
            _body.AddForce(Vector3.up * (jumpSpeed - v.y), ForceMode.VelocityChange);
        _jumpLatched = false;
    }
}
```

`CharacterController` rules:

- It is not a physics body: forces do nothing, and it pushes nothing unless
  `OnControllerColliderHit` applies an impulse to the other `Rigidbody`.
- Call `Move` exactly once per step. `isGrounded` reflects the last `Move` only.
- In `Update`, motion follows the frame rate and looks smooth. In `FixedUpdate`, it steps with the
  rest of the simulation (repeatable, testable) and needs a visual child interpolated in
  `LateUpdate`. Pick one per project.
- Teleport by disabling the controller, setting the position, and re-enabling it.

## Input System setup

1. Install `com.unity.inputsystem`. Set Project Settings > Player > Active Input Handling to Input
   System Package (New). The editor restarts.
2. Keep actions in one asset: the project-wide actions (Project Settings > Input System Package),
   read through `InputSystem.actions`, or a dedicated `.inputactions` asset in `Settings/` with
   Generate C# Class on.
3. Choose one access pattern per project:
   - `InputActionReference` serialized fields: no strings, designer-assignable.
   - The generated C# class: compile-time names.
   - `InputSystem.actions.FindAction("Player/Move")` cached in `Awake`. Never call `FindAction` per
     frame.
4. `PlayerInput` only for local multiplayer device pairing, with Behavior set to Invoke C Sharp
   Events.
5. Keep the input update mode at Process Events In Dynamic Update and latch edges for
   `FixedUpdate`.

## Reading input

Generated class, owned by one component:

```csharp
using UnityEngine;

public sealed class InputOwner : MonoBehaviour
{
    GameControls _controls; // generated from GameControls.inputactions
    public GameControls Controls => _controls;

    void Awake() => _controls = new GameControls();
    void OnEnable() => _controls.Player.Enable();
    void OnDisable() => _controls.Player.Disable();
    void OnDestroy() => _controls.Dispose();
}
```

Callbacks with a cached delegate (subscribing a method group allocates a new delegate each time):

```csharp
using System;
using UnityEngine;
using UnityEngine.InputSystem;

public sealed class InteractInput : MonoBehaviour
{
    [SerializeField] InputActionReference interact;
    Action<InputAction.CallbackContext> _onInteract;
    bool _interactLatched;

    void Awake() => _onInteract = OnInteract;
    void OnEnable() => interact.action.performed += _onInteract;
    void OnDisable() => interact.action.performed -= _onInteract;
    void OnInteract(InputAction.CallbackContext context) => _interactLatched = true;
}
```

Polling (`ReadValue<T>()`, `IsPressed()`, `WasPressedThisFrame()`) in `Update` is allocation-free
and easier to test; callbacks suit rare events.

## Rebinding

```csharp
using UnityEngine;
using UnityEngine.InputSystem;

public sealed class RebindButton : MonoBehaviour
{
    public const string PrefsKey = "input.bindings";
    [SerializeField] InputActionReference action;
    [SerializeField] int bindingIndex; // a part binding, never the composite itself
    InputActionRebindingExtensions.RebindingOperation _operation;

    public void StartRebind()
    {
        InputAction a = action.action;
        a.Disable();
        _operation = a.PerformInteractiveRebinding(bindingIndex)
            .WithControlsExcluding("<Mouse>/position")
            .WithControlsExcluding("<Mouse>/delta")
            .WithCancelingThrough("<Keyboard>/escape")
            .OnMatchWaitForAnother(0.1f)
            .OnComplete(_ => Finish(a))
            .OnCancel(_ => Finish(a))
            .Start();
    }

    void Finish(InputAction a)
    {
        _operation?.Dispose();
        _operation = null;
        a.Enable();
        PlayerPrefs.SetString(PrefsKey, a.actionMap.asset.SaveBindingOverridesAsJson());
    }

    void OnDestroy() => _operation?.Dispose();
}
```

Load overrides once at boot, before any action is enabled:

```csharp
InputActionAsset actions = InputSystem.actions; // or the game's own actions asset
if (PlayerPrefs.HasKey(RebindButton.PrefsKey))
    actions.LoadBindingOverridesFromJson(PlayerPrefs.GetString(RebindButton.PrefsKey));
```

Show bindings with `action.GetBindingDisplayString(bindingIndex)`; it follows the active device
layout and overrides.

## UI input

- uGUI: the scene's `EventSystem` uses `InputSystemUIInputModule`. A leftover
  `StandaloneInputModule` polls the legacy Input Manager.
- UI Toolkit runtime: one `UIDocument` per screen; query elements (`root.Q<Button>("play")`) in
  `OnEnable`, register callbacks there and unregister in `OnDisable`.
- Gameplay and UI action maps are separate; switching screens enables one and disables the other
  so a menu click does not fire a weapon.

## Cameras

- Cinemachine 3 (`com.unity.cinemachine`, namespace `Unity.Cinemachine`) for follow, framing and
  blends. Code written against 2.x (`Cinemachine` namespace, `CinemachineVirtualCamera`) is the old
  API; do not add more of it.
- Hand-written follow cameras move in `LateUpdate`. Following an interpolated `Rigidbody`, read
  `transform.position` (interpolated), not `Rigidbody.position` (the last physics step).
- One serialized `Camera` reference per consumer; no scattered `Camera.main`.
