
"""Instrumentacao externa QA. App/kernel originais, API real em Uvicorn."""
import json,threading,time,hashlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import uvicorn
from sqlalchemy import text
from app import main as m
from app.opencl_search import OpenCLUnavailable
state={"mode":"normal","events":[]}
lock=threading.Lock()
original_cpu=m.sequential_search
original_engine=m.opencl_engine
def revoke(conn=None):
    cfg=state["config"]
    params={"p":cfg["patient_id"],"d":cfg["dentist_id"]}
    statement=text("UPDATE clinical_access_links SET status='REVOKED',version=version+1 WHERE patient_id=:p AND dentist_id=:d AND status='ACTIVE'")
    if conn is None:
        with m.engine.begin() as db:return db.execute(statement,params).rowcount
    count=conn.execute(statement,params).rowcount;conn.commit();return count
def cpu(texts,term):
    result=original_cpu(texts,term)
    if state["mode"]=="cpu_revoke":
        count=revoke()
        state["events"].append({"point":"after_actual_cpu_comparison_before_return_to_route","revoked_rows":count})
        state["mode"]="normal"
    return result
m.sequential_search=cpu
engine=original_engine()
actual_program=engine.program
class ProgramProxy:
    @property
    def contains_bytes(self):
        real_kernel=actual_program.contains_bytes
        def call(*args,**kwargs):
            if state["mode"]!="kernel_revoke":return real_kernel(*args,**kwargs)
            # Connection prepared before enqueue, reducing observation overhead.
            with m.engine.connect() as conn:
                event=real_kernel(*args,**kwargs)
                args[0].flush()
                deadline=time.monotonic()+3
                status=event.command_execution_status
                while status>1 and time.monotonic()<deadline:
                    time.sleep(.00005);status=event.command_execution_status
                before=event.command_execution_status
                count=revoke(conn)
                after=event.command_execution_status
                event.wait()
                state["events"].append({"point":"real_contains_bytes_event_after_enqueue",
                    "event_before_commit":before,"event_after_commit":after,
                    "revocation_committed_while_event_running":before==1 and after==1,
                    "revoked_rows":count,"kernel_really_completed":event.command_execution_status==0})
                state["mode"]="normal"
                return event
        return call
engine.program=ProgramProxy()
def engine_selector():
    if state["mode"]=="unavailable":raise OpenCLUnavailable("QA injected unavailability")
    return engine
m.opencl_engine=engine_selector
class Control(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        with lock:
            state["mode"]=body["mode"];state["config"]=body;state["events"]=[]
        self.send_response(200);self.end_headers();self.wfile.write(b"ok")
    def do_GET(self):
        public={"mode":state["mode"],"events":state["events"],
                "device":engine.device_name,"platform":engine.ctx.devices[0].platform.name,
                "instrumentation":"proxy_only; original contains.cl enqueued"}
        data=json.dumps(public).encode()
        self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(data)
threading.Thread(target=ThreadingHTTPServer(("0.0.0.0",9010),Control).serve_forever,daemon=True).start()
uvicorn.run(m.app,host="0.0.0.0",port=8000,access_log=False)
