# Character animation

Choosing an animation approach, getting motion data in, and verifying motion an agent cannot watch.

## Contents

- Choosing an approach
- AnimGen
- Motion Matching and the Game Animation Sample
- Retargeting and imported motion
- Procedural layers
- Verifying motion
- Gotchas
- Sources

## Choosing an approach

| Approach | Strong at | Costs |
|---|---|---|
| State machine and blend spaces in an Animation Blueprint | Small move sets, full control, easy to debug | Hand-built transitions; grows messy with many states |
| Motion Matching (Pose Search, as in the Game Animation Sample) | High-quality locomotion from a curated library; adjustable and debuggable | Animation stays in memory; data needs careful preparation |
| AnimGen (Experimental, UE 5.8+) | Locomotion in many styles from raw motion capture; no animation data at runtime; LODs | Hours of training per iteration; less low-level control; notifies need care |
| Procedural (Control Rig, IK, physics, springs) | Secondary motion, foot placement, look-at, riders, props | Tuning by eye; needs a base animation |
| Vertex animation baked to textures | Crowds of hundreds with no skeletons | Fixed clips, no blending, no interaction |

For a jam or a first prototype: a state machine or the Game Animation Sample. AnimGen pays off
when there is a lot of motion data, many styles, or a memory budget that motion matching breaks,
and when training time fits the schedule.

## AnimGen

An Experimental plugin (UE 5.8 and later) that trains small neural networks in the editor on your
own animation data and generates the character's pose frame by frame at runtime. Trained
controllers replace the animation assets at runtime.

### Pieces

- **Animation Database**: the training data (animation sequences, raw motion capture), with a
  scripting system for inspecting and processing frames.
- **Auto-Encoder** (`UAnimGenAutoEncoder`): compresses poses into a small vector the other
  networks work in.
- **Controller** (`UAnimGenController`, a data asset): the trained network that produces poses.
  It is tied to the behaviour it was trained with. From Python: `is_valid()`, `invalidate()`,
  `frame_rate`.
- **Behaviours**: what the controller is asked to do, for example Trajectory Follow, Velocity
  Follow, Move to Target, Idle, Encoded, Tagged, Trajectory Interaction, Uncontrolled, Optional.
- **AnimGenController anim node** in the Animation Blueprint evaluates the controller; the
  character feeds it through a control object (the `MakeControlObject` node in the event graph).
- Outputs: bone transforms, attributes, Anim Notifies and Notify States. Notifies from the source
  animations are not carried over automatically; plan them as controller outputs.

### Numbers to plan with

| Item | Typical value |
|---|---|
| Data | At least 5 to 10 minutes per gait per style (walk, run; relaxed, aiming). About 5 minutes is the floor for a new style |
| Training | 4 to 18 hours, on the GPU, inside the editor |
| Runtime | About 1 ms CPU per character per frame at the top LOD, about 0.2 ms at the lowest |
| Memory | 15 to 20 MB of weights per controller, shared by every character using it |

Raw, unstructured capture works well and often better than heavily cut clips. Capturing the same
movement set facing the direction of travel and strafing gives a controller both.

### Training as an agent

- Training runs inside the editor process and its UI. Nothing outside the editor can watch it, and
  there is no resume from a checkpoint (partial results are written back to the model). Treat a
  training run as a long, unattended job: start it, leave the machine alone, check the result.
- Nothing else should use the GPU during training; minimizing the editor speeds it up. Do not run
  builds, cooks or PIE tests beside it.
- Schedule training against the plan: one iteration costs most of a working day. In a four-day jam
  that is one or two attempts at most. Start with a pre-trained controller or motion matching and
  train AnimGen in parallel only if the data is ready on day one.
- Check the GPU first: some new GPUs did not start training with the bundled PyTorch, and some
  AMD cards showed "training not started". Try a short CPU or GPU run before committing a night.
- When a run finishes, verify `controller.is_valid()` and play a scripted path before judging it.

### Tuning

| Symptom | Try |
|---|---|
| Bad quality overall | More data, more training iterations, larger networks (Hidden Unit Num). Larger networks cost runtime and memory |
| Unstable, drifts into odd poses | Raise Random Pose Sample Rate and/or Pose Noise Scale; train longer |
| Over-smoothed, stiff | Lower Random Pose Sample Rate and/or Pose Noise Scale; train longer |
| Noisy | Raise Min/Max Pose Smoothing Time on the anim node; lower Pose Noise Scale |
| Auto-encoder does not reproduce poses | Raise Base Weight Multiplier and/or Encoding Size |
| Slow walks become many small steps | The network treats gaits as similar-length cycles; train with speeds separated |
| Movement jitters in play | Project Settings, Network Prediction, Preferred Ticking Policy: Independent |
| Character T-poses | Bad input: check the control object is made in the event graph and the behaviour is fed |
| Character stays at the origin | Movement setup (Mover or Character Movement); check root motion settings on the data (Enable Root Motion, Force Root Lock) |

It works with Character Movement or Mover. It is strongest at locomotion; activities such as
cooking or bench work and pose-to-pose moves (sitting down) are possible through custom behaviours
but weaker than dedicated tools.

### Shipping

- "Missing Dependency" cook errors from AnimGen training and viewport settings classes are
  harmless; with engine source they go away by marking those classes editor-only.
- AnimGen on the web target is untested territory: 1 ms per character on desktop CPU becomes more
  in a browser. Measure before relying on it there.
- Epic's AnimGen Example on Fab is marked as not for use with AI. Agents may place and reference
  it, but must not open, edit, copy or retrain from it; the licence decision is the human's.

## Motion Matching and the Game Animation Sample

- The Game Animation Sample (GASP) is the reference setup: Pose Search databases, Choosers,
  trajectory prediction, and a large locomotion library on the UE mannequin. Start a third-person
  game from it rather than from the basic template when locomotion quality matters.
- Content copied in from other samples may need plugins it does not enable (the City Sample
  vehicles need Chaos Vehicles). Check each source project's plugin list before copying.
- Its data also trains AnimGen (Epic's tutorials compare both on the same data).

## Retargeting and imported motion

- Use an IK Rig per skeleton and an IK Retargeter between them. Batch retargeting from Python:
  `unreal.IKRetargetBatchOperation.duplicate_and_retarget(...)`. Keep the script in the repo.
- Mixamo rigs have the hips as root. A retargeter that applies root motion from that root pins the
  hips to the floor and stretches the body; map root motion explicitly.
- Generated characters (Tripo, Meshy and similar) rigged on the UE mannequin skeleton retarget
  cleanly; check bone names and the rest pose before animating.
- Preset clips often bake travel into the pelvis. Remove it, then measure the true no-slide speed
  from the removed distance and set movement speeds from that, not by eye.
- Text-to-motion tools (some are built on NVIDIA's Kimodo) produce clips that still need the same
  checks: root motion, foot contact, loop seams. Read each tool's licence and engine version.

## Procedural layers

- One spring on the pelvis driven by the vehicle's or character's acceleration, with IK legs, a
  lagging spine and pendulum arms, reads as weight shifting through the body. Movement should start
  at the centre of mass and travel out to the limbs.
- Look-at: measure which way the face points in the rest pose and use that as the forward vector.
- Riders and props: IK to sockets with a tolerance test (hands within a millimetre of the grips)
  and a release on crash.
- Crowds: bake a few clips into a texture that the material plays; no skeletons, no animation
  ticks.

## Verifying motion

An agent cannot see motion in a still. Measure it:

- **Foot slide**: planted-foot velocity as a fraction of body speed (aim for single-digit percent).
- **Contact**: foot height above the ground at touchdown (a few centimetres, not 20).
- **Alternation**: compare consecutive frames for parts that jump back and forth (heads, props).
- **Loops**: the seam frame against the first frame; looping by skipping the seam limps.
- **Playback rate and restarts**: clips that play too fast or restart on every hop.
- Record a short frame sequence of each motion and look at it as a contact sheet as well as
  numbers. The human judges the feel.

## Gotchas

- In UE 5.9 a hidden bone stops being evaluated. Hiding the mannequin's head or hand bones and
  attaching your own meshes to them makes those meshes jump every other frame. Call
  `SetAlwaysAnimateHiddenBones(true)` on the skeletal mesh component.
- A montage that is interrupted (an automatic holster, an equip) also stops its root motion. A
  climb or vault that depends on root motion drops the character. Block interrupts while it plays.
- A fall pose made of two neighbouring keys looping trembles; a clip that lifts the pelvis while
  physics also lifts the capsule leaves the feet hanging at touchdown; transitions whose automatic
  exit fires on entry blend the landing away unseen. Measure each.
- Swapping a character mesh drops sockets that gameplay uses (camera, weapon, microphone). List
  required sockets and check them after any swap.
- A first-person character often draws no body at all; making it visible is a feature with
  clipping risk, not a toggle.
- Strand hair (MetaHuman) can stall the GPU in heavy scenes; have the cheaper hair option ready.
- On the web target, a skinned mesh exposed a GPU memory leak in the 5.9 Preview. Measure memory
  with characters on and off (see [build and ship](build-and-ship.md#the-web-target-wasm)).

## Sources

- Epic, AnimGen tutorial series and FAQ: https://dev.epicgames.com/community/learning/tutorials/eGME/unreal-engine-animgen
- AnimGen community thread: https://forums.unrealengine.com/t/community-tutorial-animgen/2743773
- AnimGen Example on Fab: https://www.fab.com/listings/df37eb46-09bf-4604-9307-cdc39c769790
- MegaJam devlogs (Director's Blueprint, STILL, Stunt Launch, The Last Plan, FIX IT YOURSELF!),
  listed in [jam production](jam-production.md#sources).
