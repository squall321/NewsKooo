# systemd units (production, Ubuntu 22.04)

Run the NewsKoo API and Kafka workers as Apptainer instances under systemd.
Copy the units to `/etc/systemd/system/`, edit paths/`EnvironmentFile`, then:

```bash
sudo cp infra/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now newskoo-api.service
# one worker per pipeline stage:
sudo systemctl enable --now newskoo-worker@parser.service
sudo systemctl enable --now newskoo-worker@persist.service
sudo systemctl enable --now newskoo-worker@results.service
sudo systemctl enable --now newskoo-worker@analyzer.service
sudo systemctl enable --now newskoo-worker@issues.service
sudo systemctl enable --now newskoo-worker@ingest.service
```

Scale a stage by running multiple instances (Kafka consumer groups share the
partitions): `newskoo-worker@analyzer.service` + a drop-in, or template copies.
`/etc/newskoo.env` holds the `NEWSKOO_*` settings (see repo `.env.example`).
`SIF_DIR` defaults to `/opt/newskoo` and holds `backend.sif` / `frontend.sif`.
