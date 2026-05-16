# Expected Failure Modes

- Treating the printed number chips as layer ranks. The chips are deliberately reversed from the true draw order.
- Inferring depth from global strip color or label frequency instead of inspecting each probe.
- Reading the top strip at the nearest visible endpoint rather than at the ring center.
- Using centerline extraction only. The lower strip centerline often continues behind an upper strip, so inferred geometry can contradict visible topology.
- Over-trusting shadows. Shadows help human auditability, but exact scoring follows which colored strip is visibly on top at the contact.
- OCR-only solving. Labels are easy to OCR, but the hard step is assigning labels to local occlusion events.
