import sshtunnel
import webuiapi


ssh_username = 'root'
ssh_host = 'connect.yza1.seetacloud.com'
ssh_port = 12007
ssh_password = ''
local_port = 6006
remote_host = '127.0.0.1'
remote_port = 6006
tunnel = sshtunnel.SSHTunnelForwarder(
    (ssh_host, ssh_port),
    ssh_username=ssh_username,
    ssh_password=ssh_password,
    local_bind_address=(remote_host, local_port),
    remote_bind_address=(remote_host, remote_port),
    set_keepalive=60,
)
tunnel.start()
assert tunnel.is_active, f"SSH tunnel is not active."

api = webuiapi.WebUIApi()
api = webuiapi.WebUIApi(host='127.0.0.1', port=6006)

image = api.txt2img(
    prompt="cute squirrel",
    negative_prompt="ugly, out of frame",
    seed=42,
    width=832,
    height=1216,
    # styles=["anime"],
    cfg_scale=1.2,
    sampler_name='Euler Ancestral CFG++',
    steps=32,
).image

image.save('webuiapi.png')
