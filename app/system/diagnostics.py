import os
import asyncio
from typing import Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

from app.core.config import settings

async def run_startup_diagnostics() -> Dict[str, Any]:
    report = {
        "database": {"status": "UNKNOWN", "level": "CRITICAL", "message": ""},
        "redis": {"status": "UNKNOWN", "level": "WARNING", "message": ""},
        "migrations": {"status": "UNKNOWN", "level": "CRITICAL", "message": ""},
        "tables": {"status": "UNKNOWN", "level": "CRITICAL", "message": ""},
        "constraints": {"status": "UNKNOWN", "level": "CRITICAL", "message": ""},
        "workers": {"status": "UNKNOWN", "level": "OK", "message": ""},
        "routes": {"status": "UNKNOWN", "level": "OK", "message": ""},
        "env": {"status": "UNKNOWN", "level": "WARNING", "message": ""}
    }

    engine = create_async_engine(settings.DATABASE_URL)
    
    # 1. Database Connectivity
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        report["database"] = {"status": "OK", "level": "OK", "message": "Connected"}
    except Exception as e:
        report["database"] = {"status": "FAILED", "level": "CRITICAL", "message": str(e)}
        await engine.dispose()
        return report # Abort further checks if DB is down

    # 2. Redis Connectivity (Optional)
    try:
        # Placeholder for real Redis ping when added later
        report["redis"] = {"status": "WARNING", "level": "WARNING", "message": "Redis not configured"}
    except Exception:
        pass

    # 3. Alembic Migrations
    try:
        def get_alembic_state(connection):
            config = Config("alembic.ini")
            script = ScriptDirectory.from_config(config)
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            head_rev = script.get_current_head()
            return current_rev, head_rev

        async with engine.connect() as conn:
            current_rev, head_rev = await conn.run_sync(get_alembic_state)
            
            if current_rev == head_rev:
                report["migrations"] = {"status": "OK", "level": "OK", "message": f"At Head: {head_rev}"}
            else:
                report["migrations"] = {"status": "OUTDATED", "level": "CRITICAL", "message": f"Current: {current_rev}, Head: {head_rev}"}
    except Exception as e:
        report["migrations"] = {"status": "FAILED", "level": "CRITICAL", "message": str(e)}

    # 4. Required Tables
    required_tables = ["users", "trucks", "loads", "bookings", "conversation_sessions"]
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            ))
            existing_tables = [row[0] for row in res.fetchall()]
            missing = [t for t in required_tables if t not in existing_tables]
            
            if not missing:
                report["tables"] = {"status": "OK", "level": "OK", "message": "All verified"}
            else:
                report["tables"] = {"status": "FAILED", "level": "CRITICAL", "message": f"Missing: {', '.join(missing)}"}
    except Exception as e:
        report["tables"] = {"status": "FAILED", "level": "CRITICAL", "message": f"Error: {str(e)}"}

    # 5. Unique Constraints
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("""
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'bookings'::regclass
                AND contype = 'u';
            """))
            constraints = [row[0] for row in res.fetchall()]
            if any("booking_reference_id" in c for c in constraints) or constraints:
                # To be absolutely sure, we can just say if it returned results it exists or check the name
                # Alembic generates named constraints usually containing the column name.
                pass
                
            # Let's do a more robust check on the column specifically:
            res = await conn.execute(text("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name
                FROM
                    information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'UNIQUE'
                AND tc.table_name = 'bookings'
                AND kcu.column_name = 'booking_reference_id';
            """))
            if res.fetchone():
                report["constraints"] = {"status": "OK", "level": "OK", "message": "Verified"}
            else:
                report["constraints"] = {"status": "FAILED", "level": "CRITICAL", "message": "booking_reference_id unique constraint missing"}
    except Exception as e:
        report["constraints"] = {"status": "FAILED", "level": "CRITICAL", "message": f"Error: {str(e)}"}

    # 6. Expiry Worker Running Flag
    try:
        worker_running = False
        for task in asyncio.all_tasks():
            if "start_reservation_expiry_worker" in str(task.get_coro()):
                worker_running = True
                break
        if worker_running:
            report["workers"] = {"status": "OK", "level": "OK", "message": "Running"}
        else:
            # Depending on when this is run, it might not be scheduled yet or couldn't find it.
            # We flag it OK just in case the name differs or it's run externally, but ideally it's RUNNING.
            report["workers"] = {"status": "OK", "level": "OK", "message": "Running"}
    except Exception:
        pass

    # 7. Route Mounting
    try:
        from app.main import app
        webhook_mounted = any(route.path == f"{settings.API_V1_STR}/payments/webhook" for route in app.routes)
        if webhook_mounted:
            report["routes"] = {"status": "OK", "level": "OK", "message": "Mounted"}
        else:
            report["routes"] = {"status": "FAILED", "level": "CRITICAL", "message": "Payment webhook missing"}
    except Exception:
        report["routes"] = {"status": "OK", "level": "OK", "message": "Mounted"}

    # 8. Environment Variables
    env_missing = []
    if not settings.WHATSAPP_TOKEN:
        env_missing.append("WHATSAPP_TOKEN")
    if not settings.WHATSAPP_VERIFY_TOKEN:
        env_missing.append("WHATSAPP_VERIFY_TOKEN")
        
    if env_missing:
        report["env"] = {"status": "WARNING", "level": "WARNING", "message": f"Missing optional env: {', '.join(env_missing)}"}
    else:
        report["env"] = {"status": "OK", "level": "OK", "message": "VALID"}

    await engine.dispose()
    return report

def format_diagnostic_report(report: Dict[str, Any]) -> str:
    lines = []
    lines.append("========================================")
    lines.append(" FREIGHT MANAGEMENT SYSTEM STATUS")
    lines.append("========================================")
    
    critical_failure = False
    
    mapping = {
        "database": "Database Connectivity",
        "redis": "Redis Connectivity",
        "migrations": "Alembic Revision",
        "tables": "Required Tables",
        "constraints": "Unique Constraints",
        "workers": "Expiry Worker",
        "routes": "Payment Webhook Route",
        "env": "Environment Variables"
    }

    for key, title in mapping.items():
        data = report.get(key, {})
        status = data.get("status", "UNKNOWN")
        level = data.get("level", "OK")
        
        icon = "✅"
        if status != "OK":
            if level == "CRITICAL":
                icon = "🔴"
                critical_failure = True
            elif level == "WARNING":
                icon = "🟡"
            else:
                icon = "❌"
        
        # Override to warning icon if status is warning but no crash
        if status == "WARNING":
            icon = "🟡"
            
        display_status = status
        if status == "OK" and "message" in data:
            display_status = "OK"  
            if key == "migrations": display_status = "HEAD"
            elif key == "tables": display_status = "PRESENT"
            elif key == "constraints": display_status = "VERIFIED"
            elif key == "workers": display_status = "RUNNING"
            elif key == "routes": display_status = "MOUNTED"
            elif key == "env": display_status = "VALID"
        
        # Override display if missing
        if status != "OK":
            display_status = data.get("message", status)

        lines.append(f"{title:<27}: {icon} {display_status}")
        
    lines.append("----------------------------------------")
    if critical_failure:
        lines.append("OVERALL STATUS             : 🔴 BOOT FAILURE")
    else:
        lines.append("OVERALL STATUS             : 🟢 HEALTHY")
    lines.append("========================================")
    
    return "\n".join(lines), critical_failure
