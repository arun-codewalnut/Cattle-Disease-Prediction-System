# Playbook: Add a new disease model

1. **Data**: add/curate the dataset under `ml-service/data/<disease-name>/` (gitignored —
   document the source in a `SOURCE.md` next to it).
2. **Train**: write a training script in `ml-service/training/<disease-name>_train.py`.
   Log the run with MLflow. Save the artifact to `ml-service/models/<disease-name>_v1.pkl`
   (or `.pt`/`.onnx`), gitignored — document versions in `ml-service/models/REGISTRY.md`.
3. **Serve**: add an inference wrapper in `ml-service/app/models/<disease_name>.py`, expose
   it as a tool the LangGraph agent can call from `ml-service/app/agent/`.
4. **Route**: update the agent graph so it knows when to call this new tool (e.g. based on
   symptom keywords or image type).
5. **Contract**: if the response shape changes, update
   [docs/API_CONTRACTS.md](../../docs/API_CONTRACTS.md) and regenerate the OpenAPI spec.
6. **Test**: add a case to `ml-service/tests/` and to `tests/e2e/` if it changes the
   end-to-end flow.
