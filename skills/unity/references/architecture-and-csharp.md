# Architecture and C#

Assemblies, the domain/adapter split, data assets, state machines, determinism, allocation-free
C#, async, and serialization safety for Unity 6 projects.

## Contents

- Assemblies
- Domain and adapter
- Composition root
- ScriptableObject patterns
- State machines
- Fixed-tick simulation and determinism
- Allocation-free C#
- Pooling
- Awaitable patterns
- Serialization and renames
- Editor code

## Assemblies

Every script belongs to an assembly definition. Nothing lives in `Assembly-CSharp`: it cannot be
referenced by `.asmdef` assemblies and any change in it recompiles everything.

| Assembly | Platforms | References | Holds |
|---|---|---|---|
| `Game.Domain` | All | none | Rules, state, math. `noEngineReferences: true` |
| `Game.Runtime` | All | `Game.Domain`, package assemblies | Adapters, `ScriptableObject` types, views |
| `Game.Editor` | Editor | `Game.Runtime`, `Game.Domain` | Build script, validators, importers, menu items |
| `Game.Tests.EditMode` | Editor | the above, test runner | Domain and editor tests |
| `Game.Tests.PlayMode` | All | `Game.Runtime`, `Game.Domain`, test runner | Lifecycle, physics, input, scene tests |

Test assembly templates are in the testing reference. The three code assemblies:

`Assets/_Project/Scripts/Domain/Game.Domain.asmdef`

```json
{
  "name": "Game.Domain",
  "rootNamespace": "Game.Domain",
  "references": [],
  "includePlatforms": [],
  "excludePlatforms": [],
  "allowUnsafeCode": false,
  "overrideReferences": false,
  "precompiledReferences": [],
  "autoReferenced": true,
  "defineConstraints": [],
  "versionDefines": [],
  "noEngineReferences": true
}
```

`Assets/_Project/Scripts/Runtime/Game.Runtime.asmdef`

```json
{
  "name": "Game.Runtime",
  "rootNamespace": "Game",
  "references": [
    "Game.Domain",
    "Unity.InputSystem",
    "Unity.RenderPipelines.Core.Runtime",
    "Unity.RenderPipelines.Universal.Runtime"
  ],
  "includePlatforms": [],
  "excludePlatforms": [],
  "allowUnsafeCode": false,
  "overrideReferences": false,
  "precompiledReferences": [],
  "autoReferenced": true,
  "defineConstraints": [],
  "versionDefines": [],
  "noEngineReferences": false
}
```

`Assets/_Project/Scripts/Editor/Game.Editor.asmdef`

```json
{
  "name": "Game.Editor",
  "rootNamespace": "Game.Editor",
  "references": ["Game.Domain", "Game.Runtime"],
  "includePlatforms": ["Editor"],
  "excludePlatforms": [],
  "allowUnsafeCode": false,
  "overrideReferences": false,
  "precompiledReferences": [],
  "autoReferenced": false,
  "defineConstraints": [],
  "versionDefines": [],
  "noEngineReferences": false
}
```

Rules:

- Add package assemblies only where used (`Unity.Addressables`, `Unity.ResourceManager`,
  `Unity.Cinemachine`, `Unity.Mathematics`). An unused reference still costs compile time.
- With "Use GUIDs" on (the inspector default) Unity rewrites references as `GUID:...`, which
  survive assembly renames. Name references are fine in hand-written files.
- `Game.Domain` cannot see `UnityEngine.Vector3`. Use `System.Numerics` or small domain structs and
  convert at the adapter.
- Expose test seams with `[assembly: InternalsVisibleTo("Game.Tests.EditMode")]` (and PlayMode) in
  an `AssemblyInfo.cs`, rather than making members public.
- Renaming an assembly breaks `[SerializeReference]` data for types inside it. See
  "Serialization and renames".

## Domain and adapter

The domain is deterministic: the same inputs and `dt` sequence produce the same outputs, and it
runs in an EditMode test in microseconds.

```csharp
// Scripts/Domain/Movement/DashMotor.cs   (Game.Domain, no UnityEngine)
using System;
using System.Numerics;

namespace Game.Domain.Movement
{
    public readonly struct DashConfig
    {
        public readonly float Speed, Duration, Cooldown;
        public DashConfig(float speed, float duration, float cooldown)
        {
            Speed = speed; Duration = duration; Cooldown = cooldown;
        }
    }

    public sealed class DashMotor
    {
        readonly DashConfig _config;
        float _dashLeft, _cooldownLeft;
        Vector2 _dashDirection;

        public DashMotor(DashConfig config) => _config = config;

        public bool IsDashing => _dashLeft > 0f;

        public Vector2 Tick(float dt, Vector2 moveInput, float walkSpeed, bool dashRequested)
        {
            if (_cooldownLeft > 0f) _cooldownLeft = MathF.Max(0f, _cooldownLeft - dt);

            if (dashRequested && _cooldownLeft == 0f && moveInput.LengthSquared() > 0.01f)
            {
                _dashDirection = Vector2.Normalize(moveInput);
                _dashLeft = _config.Duration;
                _cooldownLeft = _config.Cooldown;
            }

            if (_dashLeft > 0f)
            {
                _dashLeft = MathF.Max(0f, _dashLeft - dt);
                return _dashDirection * _config.Speed;
            }

            return moveInput * walkSpeed;
        }
    }
}
```

```csharp
// Scripts/Runtime/Movement/MovementConfig.cs
using Game.Domain.Movement;
using UnityEngine;

namespace Game.Movement
{
    [CreateAssetMenu(menuName = "Game/Movement Config")]
    public sealed class MovementConfig : ScriptableObject
    {
        [SerializeField, Min(0f)] float walkSpeed = 5f;
        [SerializeField, Min(0f)] float dashSpeed = 18f;
        [SerializeField, Min(0f)] float dashDuration = 0.15f;
        [SerializeField, Min(0f)] float dashCooldown = 0.6f;

        public float WalkSpeed => walkSpeed;
        public DashConfig ToDashConfig() => new(dashSpeed, dashDuration, dashCooldown);
    }
}
```

```csharp
// Scripts/Runtime/Movement/PlayerMover.cs   (adapter: no rules, no allocations per frame)
using Game.Domain.Movement;
using UnityEngine;
using UnityEngine.InputSystem;
using NVector2 = System.Numerics.Vector2;

namespace Game.Movement
{
    [RequireComponent(typeof(Rigidbody))]
    public sealed class PlayerMover : MonoBehaviour
    {
        [SerializeField] MovementConfig config;
        [SerializeField] InputActionReference move;
        [SerializeField] InputActionReference dash;

        Rigidbody _body;
        DashMotor _motor;
        NVector2 _moveInput;
        bool _dashLatched;

        void Awake()
        {
            _body = GetComponent<Rigidbody>(); // guaranteed by RequireComponent
            _motor = new DashMotor(config.ToDashConfig());
        }

        void Update()
        {
            Vector2 m = move.action.ReadValue<Vector2>();
            _moveInput = new NVector2(m.x, m.y);
            if (dash.action.WasPressedThisFrame()) _dashLatched = true; // latch the edge
        }

        void FixedUpdate()
        {
            NVector2 v = _motor.Tick(Time.fixedDeltaTime, _moveInput, config.WalkSpeed, _dashLatched);
            _dashLatched = false; // consumed by exactly one fixed step
            _body.linearVelocity = new Vector3(v.X, _body.linearVelocity.y, v.Y);
        }

        void OnDisable() => _dashLatched = false;
    }
}
```

The adapter does not enable action maps. One owner does that (project-wide actions are enabled by
default; otherwise the input owner or composition root enables them). Two components disabling a
shared action is a common source of "input stopped working".

## Composition root

- One `Bootstrap` component per scene (or a persistent Boot scene) with
  `[DefaultExecutionOrder(-1000)]` creates domain services and hands them to adapters through an
  `internal void Construct(...)` method or serialized references.
- No `static Instance` singletons that hold game state. A cross-scene service lives on an object in
  the Boot scene that is created explicitly, never found lazily.
- Use a DI container (VContainer, Extenject) only when the project already has one.
- Execution order is declared (`[DefaultExecutionOrder]`), never inferred from hierarchy order.

## ScriptableObject patterns

Config assets are read-only at runtime: private serialized fields, public getters, validation in
`OnValidate`.

Event channel, with a cached delegate so subscribing allocates once:

```csharp
using System;
using UnityEngine;

public abstract class EventChannel<T> : ScriptableObject
{
    event Action<T> Raised;
    public void Raise(T value) => Raised?.Invoke(value);
    public void Subscribe(Action<T> handler) => Raised += handler;
    public void Unsubscribe(Action<T> handler) => Raised -= handler;
}

[CreateAssetMenu(menuName = "Game/Events/Int Channel")]
public sealed class IntEventChannel : EventChannel<int> { }
```

```csharp
using System;
using TMPro;
using UnityEngine;

public sealed class ScoreView : MonoBehaviour
{
    [SerializeField] IntEventChannel scoreChanged;
    [SerializeField] TMP_Text label;
    Action<int> _onScore;

    void Awake() => _onScore = OnScore;
    void OnEnable() => scoreChanged.Subscribe(_onScore);
    void OnDisable() => scoreChanged.Unsubscribe(_onScore);
    void OnScore(int score) => label.SetText("{0:0}", score);
}
```

Runtime set, the replacement for `FindObjectsByType` at runtime:

```csharp
using System.Collections.Generic;
using UnityEngine;

public abstract class RuntimeSet<T> : ScriptableObject
{
    readonly List<T> _items = new();
    public IReadOnlyList<T> Items => _items;
    public void Add(T item) { if (!_items.Contains(item)) _items.Add(item); }
    public void Remove(T item) => _items.Remove(item);
}
```

Members add themselves in `OnEnable` and remove themselves in `OnDisable`. Iterate `Items` with
`for`, not `foreach`, to avoid boxing the interface enumerator.

## State machines

Rules live in a pure C# state machine; the `Animator` state machine only drives visuals.

```csharp
using System;

namespace Game.Domain.Enemies
{
    public enum EnemyState { Idle, Chase, Attack, Dead }

    public sealed class EnemyBrain
    {
        readonly float _aggroRange, _attackRange;
        public EnemyState State { get; private set; } = EnemyState.Idle;
        public event Action<EnemyState, EnemyState> Changed;

        public EnemyBrain(float aggroRange, float attackRange)
        {
            _aggroRange = aggroRange; _attackRange = attackRange;
        }

        public void Tick(float distanceToTarget, bool targetAlive, int health)
        {
            EnemyState next = State switch
            {
                _ when health <= 0 => EnemyState.Dead,
                EnemyState.Dead => EnemyState.Dead,
                _ when !targetAlive => EnemyState.Idle,
                _ when distanceToTarget <= _attackRange => EnemyState.Attack,
                _ when distanceToTarget <= _aggroRange => EnemyState.Chase,
                _ => EnemyState.Idle,
            };
            if (next == State) return;
            EnemyState previous = State;
            State = next;
            Changed?.Invoke(previous, next);
        }
    }
}
```

An enum and a `switch` allocate nothing and read well in a debugger. For states with their own
data, preallocate one instance per state; never `new` a state on transition.

## Fixed-tick simulation and determinism

- Domain ticks take `dt`, inputs and a seeded RNG as parameters. They never read `Time`,
  `UnityEngine.Random`, `DateTime.Now`, or rely on `Dictionary`/`HashSet` enumeration order.
- Count time in integer ticks. Float accumulation is not exact: thirty steps of `0.02f` do not sum
  to `0.6f`, so a cooldown compared in float time can be one tick late.
- Seeded RNG for the domain:

  ```csharp
  public struct XorShift32
  {
      uint _state;
      public XorShift32(uint seed) => _state = seed == 0 ? 0x9E3779B9u : seed;
      public uint NextUInt() { _state ^= _state << 13; _state ^= _state >> 17; _state ^= _state << 5; return _state; }
      public float NextFloat01() => (NextUInt() >> 8) * (1f / 16777216f);
      public int Range(int minInclusive, int maxExclusive) =>
          minInclusive + (int)(NextUInt() % (uint)(maxExclusive - minInclusive));
  }
  ```

- PhysX with Enhanced Determinism (Physics settings) repeats results for the same build, platform,
  scene and insertion order. It is not deterministic across platforms or builds.
- Float results can differ between Mono and IL2CPP and between CPU architectures. Lockstep or
  rollback netcode needs the domain to own the simulation in fixed-point or integer math, with
  PhysX for cosmetic motion only.
- Fixed Timestep (Project Settings > Time) sets the simulation rate; Maximum Allowed Timestep caps
  catch-up after a hitch so the game slows down instead of spiralling.

## Allocation-free C#

| Pattern | Problem | Fix |
|---|---|---|
| Lambda capturing locals or `this` | New closure per call | Cache the delegate in `Awake`; `static` lambdas where no capture is needed |
| `foreach` over `IList<T>`, `IEnumerable<T>`, `IReadOnlyList<T>` | Boxed enumerator | `for` with an index; `foreach` over a concrete `List<T>` is fine |
| `params object[]`, `string.Format`, interpolation | Array and string garbage | Overloads with fixed arity; TMP `SetText` |
| Struct passed as an interface | Boxing | Generic method constrained to the interface |
| `new List<T>()` inside a method called per frame | Garbage per call | Reuse a field with `Clear()`, or `ListPool<T>.Get(out var list)` in a `using` |
| `GetComponentsInChildren<T>()` | New array | `GetComponentsInChildren(list)` overload |
| `Debug.Log($"...")` in a hot path | Formats even when unread | A `[Conditional("DEVELOPMENT_BUILD"), Conditional("UNITY_EDITOR")]` wrapper |
| `enum.ToString()`, `GetType().Name` | String allocation | Precomputed lookup arrays |
| `transform.position` then `transform.rotation` | Two native calls | `GetPositionAndRotation(out p, out r)` / `SetPositionAndRotation` |

Measure with a profiler marker:

```csharp
using Unity.Profiling;

static readonly ProfilerMarker s_Tick = new("Game.EnemyBrain.Tick");

void FixedUpdate()
{
    using (s_Tick.Auto()) { /* work */ }
}
```

## Pooling

```csharp
using UnityEngine;
using UnityEngine.Pool;

public sealed class ProjectileSpawner : MonoBehaviour
{
    [SerializeField] Projectile prefab;
    [SerializeField, Min(0)] int prewarm = 32;
    ObjectPool<Projectile> _pool;

    void Awake()
    {
        _pool = new ObjectPool<Projectile>(
            createFunc: Create,
            actionOnGet: p => p.gameObject.SetActive(true),
            actionOnRelease: p => p.gameObject.SetActive(false),
            actionOnDestroy: p => Destroy(p.gameObject),
            collectionCheck: Application.isEditor, // catches double release in the Editor only
            defaultCapacity: prewarm,
            maxSize: 256);

        var warm = new Projectile[prewarm];
        for (int i = 0; i < prewarm; i++) warm[i] = _pool.Get();
        for (int i = 0; i < prewarm; i++) _pool.Release(warm[i]);
    }

    Projectile Create()
    {
        Projectile p = Instantiate(prefab); // unparented: a moving spawner must not drag live projectiles
        p.Bind(_pool);
        return p;
    }

    public Projectile Spawn(Vector3 position, Quaternion rotation)
    {
        Projectile p = _pool.Get();
        p.transform.SetPositionAndRotation(position, rotation);
        p.Launch(); // resets velocity, lifetime, trails
        return p;
    }
}
```

The pooled object releases itself (`_pool.Release(this)`) on hit or timeout and resets every piece
of state in `Launch`, including `Rigidbody.linearVelocity`, `angularVelocity` and trail renderers
(`TrailRenderer.Clear()`).

## Awaitable patterns

```csharp
using System.Threading;
using UnityEngine;

public sealed class DoorAdapter : MonoBehaviour
{
    [SerializeField] Transform leaf;
    [SerializeField, Min(0.01f)] float openSeconds = 0.4f;

    public async Awaitable OpenAsync()
    {
        CancellationToken ct = destroyCancellationToken;
        Quaternion start = leaf.localRotation;
        Quaternion end = start * Quaternion.Euler(0f, 90f, 0f);
        for (float t = 0f; t < 1f; t += Time.deltaTime / openSeconds)
        {
            leaf.localRotation = Quaternion.Slerp(start, end, t);
            await Awaitable.NextFrameAsync(ct);
        }
        leaf.localRotation = end;
    }
}
```

```csharp
// Background work on pure data, then back to the main thread
async Awaitable<PathResult> FindPathAsync(NavGrid grid, Cell from, Cell to, CancellationToken ct)
{
    await Awaitable.BackgroundThreadAsync();
    PathResult result = Pathfinder.Solve(grid, from, to); // Game.Domain code, no Unity API
    await Awaitable.MainThreadAsync();
    ct.ThrowIfCancellationRequested();
    return result;
}
```

- Own methods return `Awaitable` or `Awaitable<T>`. `async void` is only for Unity messages and UI
  callbacks that start a flow, with a `try`/`catch` at the top.
- Catch `OperationCanceledException` at the top of a flow, nowhere else.
- `await SceneManager.LoadSceneAsync(...)` works directly; any `AsyncOperation` is awaitable.
- An `Awaitable` is pooled: store it only to await it once. To share a result, wrap it in a
  `Task` once, outside hot paths.
- Linked tokens (`CancellationTokenSource.CreateLinkedTokenSource`) allocate; create them per flow,
  not per frame.
- `Task.Delay` ignores time scale and allocates; use `Awaitable.WaitForSecondsAsync`.

## Serialization and renames

```csharp
using UnityEngine;
using UnityEngine.Serialization;

public sealed class Weapon : MonoBehaviour
{
    [FormerlySerializedAs("damage")]
    [SerializeField] int baseDamage = 10;

    // The property was called Range; its backing field name changed with it
    [field: SerializeField, FormerlySerializedAs("<Range>k__BackingField")]
    public float MaxRange { get; private set; } = 20f;
}
```

```csharp
using UnityEngine.Scripting.APIUpdating;

// Type stored with [SerializeReference]; it was Game.Items.Effect in Game.Runtime
[System.Serializable]
[MovedFrom(autoUpdateAPI: false, sourceNamespace: "Game.Items", sourceAssembly: "Game.Runtime", sourceClassName: "Effect")]
public sealed class DamageEffect : IItemEffect { /* ... */ }
```

Rename procedure:

1. Rename the field, add `[FormerlySerializedAs]`.
2. Re-save every asset that holds the type: an editor menu item that calls
   `AssetDatabase.ForceReserializeAssets(paths)` for the affected prefabs, scenes and assets.
3. Commit. `git diff` shows the new field name in YAML and unchanged values.
4. Remove the attribute in a later commit, once no branch still holds the old name.

Unity does not serialize properties (without `field:`), static or `readonly` fields,
`Dictionary<,>`, interface-typed fields (without `[SerializeReference]`), multidimensional arrays,
or nested lists. Changing a field's type keeps data only for compatible primitives; otherwise keep
the old field hidden (`[SerializeField, HideInInspector]`), migrate in an editor script, re-save,
then delete it.

Meta files: the GUID in `Foo.cs.meta` is how scenes and prefabs find `Foo`. Creating a file outside
the editor is fine (Unity generates the `.meta` on import). Deleting a `.meta`, or moving a file
without it, mints a new GUID and silently breaks every reference.

## Editor code

- All editor code lives in `Game.Editor`. A runtime assembly that imports `UnityEditor` fails the
  player build. `#if UNITY_EDITOR` in runtime code is for small debug hooks only.
- Data validators run as menu items and in batch mode:

  ```csharp
  using UnityEditor;
  using UnityEngine;

  namespace Game.Editor
  {
      public static class DataValidator
      {
          [MenuItem("Tools/Game/Validate Data")]
          public static void ValidateMenu() => Validate();

          // Unity -batchmode -quit -projectPath "$PWD" -executeMethod Game.Editor.DataValidator.ValidateBatch
          public static void ValidateBatch() => EditorApplication.Exit(Validate() ? 0 : 1);

          static bool Validate()
          {
              bool ok = true;
              foreach (string guid in AssetDatabase.FindAssets("t:MovementConfig"))
              {
                  string path = AssetDatabase.GUIDToAssetPath(guid);
                  var config = AssetDatabase.LoadAssetAtPath<Game.Movement.MovementConfig>(path);
                  if (config.WalkSpeed <= 0f) { Debug.LogError($"{path}: WalkSpeed must be > 0", config); ok = false; }
              }
              return ok;
          }
      }
  }
  ```

- `OnValidate` clamps and checks values. It never creates, destroys or reparents objects.
- Asset import rules (texture compression, audio load type, model scale) belong in an
  `AssetPostprocessor`, not in a checklist.
