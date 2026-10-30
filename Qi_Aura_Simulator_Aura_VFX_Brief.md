# Aura VFX Brief — Sol's RNG-Quality Auras

Status: **in progress, one element at a time.**

| Pet | Aura | Module |
| --- | --- | --- |
| Aqua Wisp | **Tidecaller Sanctum** (done): a water lotus seat, tidal vortex ribbons, orbiting droplets, spirit koi, a breaking-wave crown, water spouts and a caustic pool | `src/client/TidecallerAura.lua` |
| Ember Wyrm | **Ember Crucible** (rebuilt): fast-spinning ground slashes and ember cloud, rising debris and sparkles, a twin vortex of energy beams, ember body flames, orbit trails, the spirit bead wyrm and the molten fire halo | `src/client/EmberCrucibleAura.lua` |

Each finished aura is its own module with the `CharacterAura` interface (build, show, hide, pulse,
update, destroy), built on the shared helpers in `src/client/AuraKit.lua` and registered in `DESIGNS`
in `src/client/CharacterAura.lua`. Its settings live in
`AuraStyles`, and its meshes in `ReplicatedStorage.AuraMeshes`; without the meshes the pet falls
back to the flame aura.

## Direction notes

- Each pet element must have its **own aura concept and effects**, not one shared aura recoloured.
  For example, Aqua Wisp (blue) should be a **water-type** aura.
- Today's character aura (`src/client/CharacterAura.lua`) is a single anime flame aura that only
  changes colour per element; it is the starting point to replace or extend.
- Pets keep their current auras (`src/client/AuraBuilder.lua`).

## The brief

ROBLOX ANIME RPG — SOL'S RNG-QUALITY AURA VFX

I want you to redesign and upgrade my Roblox game's aura VFX to the visual quality of the aura showcases in Sol's RNG. I want that same level of creativity, detail, cinematic presentation, and impressive 3D effects, but with original aura designs for my own game.

You have creative freedom. Do not limit yourself to basic Roblox ParticleEmitters or simple neon parts. You are allowed to use Blender to create custom 3D models, meshes, animated objects, textures, and other assets. You may modify, replace, or completely redesign my existing VFX if it improves the final result.

### 1. Inspect my project first

- Examine my existing aura system, character rig, scripts, and assets.
- Identify what looks basic, outdated, unfinished, or visually weak.
- Understand how the existing system works before modifying it.
- Make the actual changes wherever your tools allow.

### 2. Create spectacular aura designs

I want auras that feel like complete visual experiences surrounding the character, not just glowing particles.

Explore creative combinations of:

- Large floating 3D structures, rings, halos, weapons, wings, crystals, and other thematic objects.
- Orbiting objects with different speeds, rotations, and movement patterns.
- Layered energy flames, flowing ribbons, lightning, glowing particles, and animated trails.
- Ground circles, runes, shockwaves, energy pillars, and environmental effects.
- Custom Blender meshes and animated geometry that give each aura a distinctive silhouette.
- Dynamic lighting, emissive materials, transparency, color transitions, and atmospheric effects.
- Floating symbols, magical formations, celestial objects, and dramatic effects when appropriate.

Do not force every effect into every aura. Design each one around a strong visual concept.

### 3. Make the animation feel alive

Every component should have purposeful motion. Combine rotation, orbiting, floating, pulsing, scaling, fading, particles, and smooth animation curves. Make the aura feel dynamic from every camera angle, with visual layers moving at different speeds and distances.

Create polished activation effects, idle loops, charging sequences, power surges, and deactivation effects where appropriate.

### 4. Use Blender and Roblox together

Use Blender whenever custom geometry or animation can improve the result. Create and import assets as needed, then integrate them into Roblox Studio using appropriate meshes, attachments, particles, beams, trails, lighting, and scripts.

You are not restricted to my current assets or implementation. Find the best practical approach for the intended visual result.

### 5. Make the auras feel rare and memorable

Design an extensible system where different auras can have different levels of visual complexity, scale, effects, and presentation. A powerful or prestigious aura should feel extraordinary because of its composition, animation, detail, and visual impact, not merely because it has more particles.

Use original concepts instead of directly copying specific Sol's RNG aura designs or assets.

### 6. Actually implement the changes

Do not stop at suggestions, mockups, or example code. Modify the existing project and create the necessary assets wherever possible. Write complete Luau scripts, configure the required objects, and integrate the effects with my current character system.

If you cannot directly access Roblox Studio or Blender, use the tools and files available to produce the actual assets and implementation you can, and clearly identify any remaining manual steps.

### 7. Polish and optimize

Make the effects look excellent in-game while maintaining performance. Handle character respawning, effect cleanup, multiplayer visibility, and lower-end devices. Use local cosmetic effects where appropriate and avoid unnecessary server replication.

Test the results whenever possible, fix visible issues, and refine the animation and composition.

**FINAL GOAL:** I want my Roblox game to have original, breathtaking, Sol's RNG-quality aura VFX with custom 3D assets, intricate animated details, floating structures, beautiful particles, and cinematic presentation. Take initiative, experiment with different techniques, and prioritize the best visual result over the simplest implementation.
