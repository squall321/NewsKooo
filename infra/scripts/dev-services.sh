#!/usr/bin/env bash
# Dev services for NewsKoo on WSL Ubuntu: PostgreSQL 16 (+pgvector), Redis,
# Kafka (KRaft). Native installs for dev speed; prod uses Apptainer (infra/apptainer).
#
# Usage:
#   bash infra/scripts/dev-services.sh install   # one-time: install packages
#   bash infra/scripts/dev-services.sh up        # start postgres+redis+kafka
#   bash infra/scripts/dev-services.sh down       # stop them
#   bash infra/scripts/dev-services.sh status
#   bash infra/scripts/dev-services.sh psql       # open psql to the newskoo db
set -euo pipefail

PG_VERSION=16
KAFKA_VERSION=3.8.1
SCALA_VERSION=2.13
KAFKA_HOME=/opt/kafka
KAFKA_DATA=/var/lib/newskoo-kafka
KAFKA_LOG=/var/log/newskoo-kafka.log
export DEBIAN_FRONTEND=noninteractive

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

cmd_install() {
  log "Add PostgreSQL PGDG apt repo"
  apt-get install -y curl ca-certificates gnupg lsb-release
  install -d /usr/share/postgresql-common/pgdg
  curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc
  echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] \
https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
    > /etc/apt/sources.list.d/pgdg.list
  apt-get update -y

  log "Install PostgreSQL ${PG_VERSION} + pgvector + Redis + JRE"
  apt-get install -y \
    "postgresql-${PG_VERSION}" "postgresql-${PG_VERSION}-pgvector" \
    redis-server default-jre-headless wget

  log "Download Kafka ${KAFKA_VERSION} (KRaft)"
  if [ ! -d "$KAFKA_HOME" ]; then
    wget -q "https://downloads.apache.org/kafka/${KAFKA_VERSION}/kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz" \
      -O /tmp/kafka.tgz
    mkdir -p "$KAFKA_HOME"
    tar -xzf /tmp/kafka.tgz -C "$KAFKA_HOME" --strip-components=1
  fi
  log "install complete — run 'up' next"
}

cmd_up() {
  log "Start PostgreSQL"
  service postgresql start || pg_ctlcluster "$PG_VERSION" main start || true
  # Ensure role, db, extensions.
  sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='newskoo'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE ROLE newskoo LOGIN PASSWORD 'newskoo';"
  sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='newskoo'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE newskoo OWNER newskoo;"
  sudo -u postgres psql -d newskoo -c "CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS pg_trgm;"

  log "Start Redis"
  service redis-server start || redis-server --daemonize yes

  log "Start Kafka (KRaft)"
  if ! "$KAFKA_HOME/bin/kafka-broker-api-versions.sh" --bootstrap-server localhost:9092 >/dev/null 2>&1; then
    mkdir -p "$KAFKA_DATA"
    if [ ! -f "$KAFKA_DATA/meta.properties" ]; then
      CLUSTER_ID="$("$KAFKA_HOME/bin/kafka-storage.sh" random-uuid)"
      sed -e "s#^log.dirs=.*#log.dirs=${KAFKA_DATA}#" \
        "$KAFKA_HOME/config/kraft/server.properties" > /tmp/kraft-server.properties
      "$KAFKA_HOME/bin/kafka-storage.sh" format -t "$CLUSTER_ID" \
        -c /tmp/kraft-server.properties --ignore-formatted
    fi
    nohup "$KAFKA_HOME/bin/kafka-server-start.sh" /tmp/kraft-server.properties \
      >"$KAFKA_LOG" 2>&1 &
    echo "Kafka starting (log: $KAFKA_LOG)"
  fi
  log "up complete"
}

cmd_down() {
  log "Stop Kafka"; "$KAFKA_HOME/bin/kafka-server-stop.sh" || true
  log "Stop Redis"; service redis-server stop || true
  log "Stop PostgreSQL"; service postgresql stop || true
}

cmd_status() {
  echo "PostgreSQL:"; pg_lsclusters 2>/dev/null || service postgresql status || true
  echo "Redis:"; redis-cli ping 2>/dev/null || echo "  down"
  echo "Kafka:"; "$KAFKA_HOME/bin/kafka-broker-api-versions.sh" \
    --bootstrap-server localhost:9092 >/dev/null 2>&1 && echo "  up" || echo "  down"
}

cmd_psql() { PGPASSWORD=newskoo psql -h localhost -U newskoo -d newskoo; }

case "${1:-}" in
  install) cmd_install ;;
  up)      cmd_up ;;
  down)    cmd_down ;;
  status)  cmd_status ;;
  psql)    cmd_psql ;;
  *) echo "usage: $0 {install|up|down|status|psql}"; exit 2 ;;
esac
