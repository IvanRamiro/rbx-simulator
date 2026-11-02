---
type: pipeline
tags: [roblox, ugc, layered-clothing, blender]
created: 2026-11-02
---

# Roblox Layered Clothing Pipeline

How to make marketplace-ready Roblox layered clothing (and accessories worn over it) from Blender,
as built and tested for the [[Eclipse Exorcist Outfit]]. The scripts are in
`tools/blender/ugc/eclipse_exorcist/` (`ee_kit`, `ee_bake`, `ee_export`, `run_all`).

## Roblox's rules (checked on create.roblox.com, November 2026)

- One mesh per item, at most 4,000 triangles, watertight (no holes or exposed backfaces), quads
  where possible.
- Clothing fits in 8 x 8 x 8 studs round its attachment.
- Textures up to 2,048 (images uploaded from Studio come back at 1,024).
- Skinned to an R15 armature, at most 4 bones a vertex.
- Cages `<Item>_InnerCage` and `<Item>_OuterCage`, from Roblox's templates: their vertices and
  UVs must not be added or removed; cage UVs must match the template.
- The item must lie inside its outer cage, and the outer cage must hug it (not too loose).
- Attachments: tops `BodyFrontAttachment`, bottoms `WaistCenterAttachment`.
- Accessory: Material Plastic, Transparency 0, no extra objects.

## Reference files

Download from create.roblox.com/docs/avatar/resources:
- `Clothing_Cage_Templates.zip`
- `Rig_and_Attachments_Templates.zip`
- `BlockyCharacter.fbx`
- `Additional-FBX-assets.zip` (caged examples to copy the structure from)

**Import only their FBX files. Never open their .blend files: a .blend can carry scripts.**

## Steps

1. **Pick the body the item is shaped on.** For the blocky body,
   `ee_export.setup_reference` moves the template cage's vertices onto the blocky body's cage
   by UV. The two layouts match exactly (5,410 corners), and the template's topology and UVs
   stay untouched, so the result is a valid inner cage that fits the blocky body exactly.
2. **Model each piece twice from the same shape functions:** dense for the bake, and a clean
   game mesh within budget. Solidify both into closed shells; the inner faces take the lining.
3. **Put printed motifs on as projected geometry decals,** baked in for crisp edges, never noise.
   Each motif must lie on a single piece.
4. **Bake per piece:** each game-mesh piece from its own high-detail piece and its motifs, into
   one shared UV layout (the lining's islands at a third of the density).
5. **Export** (`ee_export.layered`):
   - copy the blocky armature, keeping the 17 R15 bones;
   - weight each piece by its own rule (sleeves follow the arms, skirts the legs, the collar the
     head);
   - join the pieces;
   - build the outer cage;
   - add the attachment marker;
   - write the FBX: armature, skinned mesh, marker, and a `_Cage` empty holding both cages.
6. **Import into Studio** with the 3D Importer, default settings. It gives a MeshPart with a
   WrapLayer, an Attachment and a SurfaceAppearance.
7. **Make the Accessory:**
   - rename the MeshPart `Handle` and remove the importer's stray Motor6D;
   - rename the attachment to Roblox's name (`BodyFrontAttachment`);
   - set all four maps on the SurfaceAppearance;
   - set the AccessoryType;
   - set the WrapLayer Order.

## Lessons (measured)

- **Outer cage on a blocky-fitted cage:** where the body's boxes meet (head and torso, torso and
  arms, torso and legs, the two legs), the template folds flat inside the body, and its vertices
  there have nonsense normals.
  - Leave those vertices alone (`blocky_internal`).
  - Judge coverage per cage vertex, not by the nearest face: the nearest face can be an inner
    fold.
  - Cover each point with the cage vertex it lies most squarely in front of, weighted by
    distance.
  - Earlier attempts pushed fold vertices 8 studs out, or moved the shoulder tops into the head.
- **Layer order:** the importer gives every WrapLayer Order 1, so pants wrap over a jacket and
  hide its skirt. Set pants 3, jacket 8, anything worn over the jacket higher (10). Changing
  Order on an item already worn doesn't re-layer it: re-equip it.
- **Don't wear a rigid accessory over layered clothing.** A rigid accessory scales with the body;
  layered cloth keeps its real thickness. On a narrow body (width 0.81) a rigid belt over the
  robe disappeared inside it. Make anything worn over clothing layered, with its inner cage set
  to the outer cage of the item it's modelled on: it then sits on that item on any body, and
  tightens onto the body when worn alone.
- Name collisions in Blender give "Name.001"; Roblox reads cages by exact name. The exporter
  claims exact names and asserts them before writing.
- Test on the owner's real avatar (scaled) and on a default blocky dummy
  (`Players:CreateHumanoidModelFromDescription(HumanoidDescription.new(), R15)`), standing,
  walking and mid-jump.

Related: [[Eclipse Exorcist Outfit]], [[Asset Workflow]].
