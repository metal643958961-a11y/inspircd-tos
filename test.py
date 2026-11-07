"""Acceptance on a dedicated, authorized Linux Docker host with the pinned image."""
import hashlib, json, os, platform, secrets, socket, subprocess as sp, sys, tarfile, tempfile, time
from pathlib import Path

def run(*a):
    return sp.check_output(a,text=True).strip()
def check(condition,message):
    if not condition: raise RuntimeError(message)
    print('PASS',message,flush=True)
def client(nick,pw,accept=True):
    s=socket.create_connection(('127.0.0.1',16667),2);s.settimeout(12)
    f=s.makefile('rb')
    send=lambda x:s.sendall((x+'\r\n').encode())
    def until(fragment):
        while True:
            msg=f.readline(4096).decode()
            if not msg:raise EOFError('server disconnected')
            if msg.startswith('PING '):send('PONG '+msg[5:].strip())
            if fragment in msg:return msg
    send('PASS '+pw);send('NICK '+nick);send('USER pilot 0 * :Synthetic')
    until(' 001 ' if accept else ' 464 ')
    return s,f,send,until

def main(path):
    check(not run('docker','ps','-aq','--filter','name=^/inspircd$'),'container name free')
    with socket.socket() as probe:probe.bind(('127.0.0.1',16667))
    print('HOST',platform.machine(),run('docker','version','--format','{{.Server.Version}}'),run('docker','compose','version','--short'))
    print('PACKAGE',hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)
    project='tm4'+secrets.token_hex(5)
    with tempfile.TemporaryDirectory(prefix=project) as td:
        here=Path.cwd();os.chdir(td)
        d=lambda *a:run('docker','compose','-p',project,*a)
        sockets=[];started=False
        try:
            with tarfile.open(path) as t:Path('docker-compose.yml').write_bytes(t.extractfile('docker-compose.yml').read())
            os.environ.pop('IRC_SECRET',None)
            check(sp.run(['docker','compose','-p',project,'config','-q'],capture_output=True).returncode!=0,'missing secret rejected')
            pw=secrets.token_hex(32);os.umask(0o077);Path('.env').write_text('IRC_SECRET='+pw+'\n')
            image=json.loads(d('config','--format','json'))['services']['inspircd']['image']
            check(run('docker','image','inspect','-f','{{.Os}}/{{.Architecture}}',image)=='linux/amd64','pinned linux/amd64 image present')
            started=True;d('up','-d','--pull','never')
            def ready(nick):
                for _ in range(25):
                    try:return client(nick,pw)
                    except (OSError,EOFError):time.sleep(.3)
                raise RuntimeError('server did not register client')
            a=ready('pilotA');sockets.append(a)
            z=json.loads(run('docker','inspect','inspircd'))[0];h=z['HostConfig']
            check(z['Config']['Image']==image and z['Config']['User']=='10000:10000' and h['ReadonlyRootfs'] and 'ALL' in h['CapDrop'] and any('no-new-privileges' in v for v in h['SecurityOpt']) and h['PortBindings']=={'6667/tcp':[{'HostIp':'127.0.0.1','HostPort':'16667'}]},'runtime identity, hardening and loopback-only port')
            wrong=client('pilotBad','incorrect',False);sockets.append(wrong);check(True,'wrong password rejected with IRC 464')
            b=ready('pilotB');sockets.append(b)
            for c in (a,b):c[2]('JOIN #pilot');c[3](' 366 ')
            a[2]('PRIVMSG #pilot :synthetic-channel');b[3]('PRIVMSG #pilot :synthetic-channel')
            b[2]('PRIVMSG pilotA :synthetic-private');a[3]('PRIVMSG pilotA :synthetic-private')
            check(True,'two authenticated clients exchange channel and direct messages')
            d('down');d('up','-d','--pull','never')
            sockets.append(ready('pilotC'));check(True,'new client registers after recreation')
        finally:
            for c in sockets:c[1].close();c[0].close()
            if started:d('down','--volumes')
            os.chdir(here)
    check(not run('docker','ps','-aq','--filter','label=com.docker.compose.project='+project) and not run('docker','network','ls','-q','--filter','label=com.docker.compose.project='+project),'own project removed')
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
