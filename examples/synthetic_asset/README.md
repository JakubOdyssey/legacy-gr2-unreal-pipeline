# Seven-joint articulated blocks

One original mesh: 48 vertices and 72 triangles. Six boxes use seven named joints, including an unweighted attachment, and 68 positive influences. Geometry, UVs, normals, bind transforms and weights are generated from simple dimensions and formulas.

The two clips, `idle` and `stride`, have 17 samples each and are independent synthetic motions. They exercise constant/identity components, procedural vertical root motion, signed/nonuniform scale and an artificial off-diagonal S term. An unrelated descriptor vector and unbound marker remain sidecar data; neither moves the actor or becomes an extra bone.

Authoring values are rounded to 12 decimal places for repeatability across common platform math libraries. This policy applies only to the newly authored fixture. The neutral schema and independent reader tests still measure the resulting reference/animation errors; rounding is not applied to any external source.

The small pose/transport error here does not establish compatibility with all legacy assets, compressed curves or Unreal runtime evaluation. See [validation](../../docs/validation.md) for the precise scope.
