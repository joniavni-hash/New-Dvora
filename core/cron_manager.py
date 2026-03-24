#!/usr/bin/env python3
"""
Cron Manager - Safe, atomic JSON operations for cron jobs
Solves the edit tool failures and race conditions
"""

import json
import os
import tempfile
import shutil
import fcntl
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class CronJobManager:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get("DVORAH_WORKSPACE", 
                                                             Path.home() / ".openclaw" / "workspace"))
        self.cron_dir = Path.home() / ".openclaw" / "cron"
        self.jobs_file = self.cron_dir / "jobs.json"
        self.lock_file = self.cron_dir / ".jobs.lock"
        
        # Ensure directory exists
        self.cron_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        # Ensure jobs.json exists with valid structure
        self._ensure_jobs_file()
    
    def _ensure_jobs_file(self):
        """Ensure jobs.json exists with valid structure"""
        if not self.jobs_file.exists():
            default_structure = {
                "version": 1,
                "jobs": []
            }
            self._write_jobs_atomic(default_structure)
            self.jobs_file.chmod(0o600)
        else:
            # Validate existing file
            try:
                with open(self.jobs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Ensure required structure
                if "version" not in data:
                    data["version"] = 1
                if "jobs" not in data:
                    data["jobs"] = []
                
                # Write back if we had to fix structure
                self._write_jobs_atomic(data)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                # File is corrupted, create backup and recreate
                backup_file = self.cron_dir / f"jobs.json.backup.{int(time.time())}"
                if self.jobs_file.exists():
                    shutil.copy2(self.jobs_file, backup_file)
                
                print(f"Warning: jobs.json corrupted, backed up to {backup_file}")
                default_structure = {"version": 1, "jobs": []}
                self._write_jobs_atomic(default_structure)
    
    def _write_jobs_atomic(self, data: Dict[str, Any]):
        """Atomic write to prevent corruption"""
        # Write to temp file first
        temp_file = self.cron_dir / f".jobs.json.tmp.{os.getpid()}"
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            
            # Atomic move
            temp_file.chmod(0o600)
            shutil.move(str(temp_file), str(self.jobs_file))
            
        except Exception as e:
            # Clean up temp file on failure
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _acquire_lock(self, timeout: float = 5.0) -> Optional[int]:
        """Acquire exclusive lock on jobs file"""
        try:
            lock_fd = os.open(str(self.lock_file), os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
            
            # Try to acquire lock with timeout
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return lock_fd
                except BlockingIOError:
                    time.sleep(0.1)
            
            # Timeout
            os.close(lock_fd)
            return None
            
        except Exception:
            return None
    
    def _release_lock(self, lock_fd: int):
        """Release lock"""
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)
            if self.lock_file.exists():
                self.lock_file.unlink()
        except:
            pass  # Best effort cleanup
    
    def read_jobs(self) -> Dict[str, Any]:
        """Safely read jobs with locking"""
        lock_fd = self._acquire_lock()
        if lock_fd is None:
            raise RuntimeError("Could not acquire lock on cron jobs file")
        
        try:
            with open(self.jobs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        finally:
            self._release_lock(lock_fd)
    
    def write_jobs(self, jobs_data: Dict[str, Any]) -> bool:
        """Safely write jobs with locking"""
        lock_fd = self._acquire_lock()
        if lock_fd is None:
            print("Warning: Could not acquire lock, skipping write")
            return False
        
        try:
            # Validate structure
            if "version" not in jobs_data:
                jobs_data["version"] = 1
            if "jobs" not in jobs_data:
                jobs_data["jobs"] = []
            
            # Atomic write
            self._write_jobs_atomic(jobs_data)
            return True
            
        except Exception as e:
            print(f"Error writing cron jobs: {e}")
            return False
        finally:
            self._release_lock(lock_fd)
    
    def add_job(self, job_data: Dict[str, Any]) -> bool:
        """Add a new job"""
        try:
            jobs = self.read_jobs()
            
            # Generate ID if not present
            if "id" not in job_data:
                import uuid
                job_data["id"] = str(uuid.uuid4())
            
            # Add timestamps
            now_ms = int(time.time() * 1000)
            if "createdAtMs" not in job_data:
                job_data["createdAtMs"] = now_ms
            job_data["updatedAtMs"] = now_ms
            
            jobs["jobs"].append(job_data)
            return self.write_jobs(jobs)
            
        except Exception as e:
            print(f"Error adding job: {e}")
            return False
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing job"""
        try:
            jobs = self.read_jobs()
            
            for job in jobs["jobs"]:
                if job["id"] == job_id:
                    job.update(updates)
                    job["updatedAtMs"] = int(time.time() * 1000)
                    return self.write_jobs(jobs)
            
            print(f"Job {job_id} not found")
            return False
            
        except Exception as e:
            print(f"Error updating job {job_id}: {e}")
            return False
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        try:
            jobs = self.read_jobs()
            original_count = len(jobs["jobs"])
            
            jobs["jobs"] = [job for job in jobs["jobs"] if job["id"] != job_id]
            
            if len(jobs["jobs"]) < original_count:
                return self.write_jobs(jobs)
            else:
                print(f"Job {job_id} not found")
                return False
                
        except Exception as e:
            print(f"Error deleting job {job_id}: {e}")
            return False
    
    def list_jobs(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """List jobs with optional filtering"""
        try:
            jobs = self.read_jobs()
            job_list = jobs["jobs"]
            
            if enabled_only:
                job_list = [job for job in job_list if job.get("enabled", False)]
            
            return job_list
            
        except Exception as e:
            print(f"Error listing jobs: {e}")
            return []
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific job"""
        try:
            jobs = self.read_jobs()
            for job in jobs["jobs"]:
                if job["id"] == job_id:
                    return job
            return None
            
        except Exception as e:
            print(f"Error getting job {job_id}: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Check cron system health"""
        try:
            # Test read
            jobs = self.read_jobs()
            
            # Test write (no-op update)
            test_success = self.write_jobs(jobs)
            
            # File stats
            stat = self.jobs_file.stat()
            
            return {
                "status": "healthy",
                "file_exists": True,
                "file_readable": True,
                "file_writable": test_success,
                "job_count": len(jobs.get("jobs", [])),
                "file_size": stat.st_size,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:],
                "error": None
            }
            
        except Exception as e:
            return {
                "status": "error",
                "file_exists": self.jobs_file.exists(),
                "file_readable": False,
                "file_writable": False,
                "job_count": 0,
                "error": str(e)
            }

# Global instance
cron_manager = CronJobManager()

def main():
    """CLI interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  cron_manager.py health                 # Check health")
        print("  cron_manager.py list [--enabled]       # List jobs")
        print("  cron_manager.py get <job_id>           # Get specific job")
        print("  cron_manager.py delete <job_id>        # Delete job")
        return
    
    command = sys.argv[1]
    
    if command == "health":
        health = cron_manager.health_check()
        print("🔍 Cron System Health Check:")
        for key, value in health.items():
            status_emoji = "✅" if key != "error" and value not in [False, None, 0] else "❌"
            if key == "error" and value is None:
                status_emoji = "✅"
            print(f"  {status_emoji} {key}: {value}")
    
    elif command == "list":
        enabled_only = "--enabled" in sys.argv
        jobs = cron_manager.list_jobs(enabled_only)
        print(f"📋 Cron Jobs ({len(jobs)} total):")
        for job in jobs:
            status = "✅" if job.get("enabled", False) else "⏸️"
            print(f"  {status} {job['name']} ({job['id']})")
            print(f"     {job.get('description', 'No description')}")
    
    elif command == "get" and len(sys.argv) > 2:
        job_id = sys.argv[2]
        job = cron_manager.get_job(job_id)
        if job:
            print(f"📄 Job: {job['name']}")
            print(json.dumps(job, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Job {job_id} not found")
    
    elif command == "delete" and len(sys.argv) > 2:
        job_id = sys.argv[2]
        if cron_manager.delete_job(job_id):
            print(f"✅ Deleted job {job_id}")
        else:
            print(f"❌ Failed to delete job {job_id}")
    
    else:
        print("❌ Unknown command or missing arguments")

if __name__ == "__main__":
    main()