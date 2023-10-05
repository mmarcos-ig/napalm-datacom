import paramiko
import socket
import time
from re import findall, sub

from netmiko.exceptions import (
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
    ConfigInvalidException,
    ReadException,
    ReadTimeout,
)

from netmiko.channel import Channel, SSHChannel, TelnetChannel, SerialChannel

class BaseConnection:
    def __init__(
        self,
        ip: str = "",
        host: str = "",
        username: str = "",
        password: str = "",
        port: int = 22,
        device_type: str = "Datacom",
        protocol: str = "SSH",
        auto_connect: bool = True,
        encoding: str = "utf-8",
        timeout: int = 60,

    ) -> None:
        
        if ip:
            self.host = ip.strip()
        elif host:
            self.host = host.strip()
        if not ip and not host and "serial" not in device_type:
            raise ValueError("Either ip or host must be set")
        if port is None:
            if "telnet" in device_type:
                port = 23
            else:
                port = 22
        self.port = int(port)

        self.username = username
        self.password = password

        self.protocol = protocol
        self.auto_connect = auto_connect
        self.timeout = timeout

        self.encoding = encoding

        # Establish the remote connection
        if auto_connect:
            self._open()

    def _open(self) -> None:
        """Decouple connection creation from __init__ for mocking."""
        self.establish_connection()
        self._try_session_preparation()

    def disconnect(self) -> None:
        """Try to gracefully close the session."""
        try:
            if self.protocol == "ssh":
                self.paramiko_cleanup()
        except Exception:
            # There have been race conditions observed on disconnect.
            pass
        finally:
            self.SSH_shell = None

    def establish_connection(self) -> None:
        self.channel: Channel
        if self.protocol == "telnet":
            pass
        elif self.protocol == "serial":
            pass
        elif self.protocol == "SSH":
            ssh_connect_params = {
                "hostname": self.host,
                "port": self.port,
                "username": self.username,
                "password": self.password
            }
            self.remote_conn_pre = paramiko.SSHClient()
            self.remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # initiate SSH connection
            try:
                self.remote_conn_pre.connect(**ssh_connect_params)
            except socket.error as conn_error:
                self.paramiko_cleanup()
                
                msg = f"""TCP connection to device failed."""

                # Handle DNS failures separately
                if "Name or service not known" in str(conn_error):
                    msg = (
                        f"DNS failure--the hostname you provided was not resolvable."
                    )

                msg = msg.lstrip()
                raise NetmikoTimeoutException(msg)
            except paramiko.ssh_exception.AuthenticationException as auth_err:
                self.paramiko_cleanup()
                msg = f"""Authentication to device failed."""

                raise NetmikoAuthenticationException(msg)
            except paramiko.ssh_exception.SSHException as e:
                self.paramiko_cleanup()
                if "No existing session" in str(e):
                    msg = (
                        "Paramiko: 'No existing session' error: "
                        "try increasing 'conn_timeout' to 15 seconds or larger."
                    )
                    raise NetmikoTimeoutException(msg)
                else:
                    msg = f""" A paramiko SSHException occurred during connection creation: {str(e)} """
                    raise NetmikoTimeoutException(msg)

            # Use invoke_shell to establish an 'interactive session'
            self.SSH_shell = self.remote_conn_pre.invoke_shell()

            self.channel = SSHChannel(conn=self.SSH_shell, encoding=self.encoding)

    def write_channel(self):
        pass

    def _try_session_preparation(self) -> None:
        try:
            self.session_preparation()
        except Exception:
            self.disconnect()
            raise

    def session_preparation(self, get_profile = True) -> None:
        """
        Prepare the session after the connection has been established

        This method handles some differences that occur between various devices
        early on in the session.

        In general, it should include:
        self._test_channel_read(pattern=r"some_pattern")
        self.set_base_prompt()
        """
        self._test_channel_read() # not implemented
        self.set_base_prompt()
        self.set_profile()

    def set_base_prompt(self):
        try:
            a, b, c = [], [], []
        
            # send three returns and store outputs in a list
            for i in range(3):
                self.SSH_shell.send("\n")

                while not self.SSH_shell.recv_ready():
                    pass
                resp = sub("\s","", self.SSH_shell.recv(65535).decode('utf-8') )
                a.append(resp)
                time.sleep(1)

            # detects duplicates, splits them, and adds them to a list
            for x in a:
                if x not in ["", None]:
                    for y in [5,4,3,2,1]: # checks for up to 5 duplicates
                        z = [x[i:i+len(x) // y] for i in range(0, len(x), len(x) // y)]
                        if all([u == z[0] for u in z]):
                            b.extend(z)
                            break

            for i in range(len(list(set(b)))):
                for j in range(len(list(set(b)))):
                    if b[i] in b[j] and i != j:
                        b.append(b[i])
                        b.pop(j)

            if len(b) > 0 and all( [x == b[0] for x in b] ):
                self.prompt = b[0]
        except:
            print("Failed to obtain prompt.")
            prompt = ""

    def set_profile(self):
        pass

    def _test_channel_read(self):
        pass

    def send_command(self, command_string, expect_string = None, loop_delay = 0.5):

        data = ""

        if expect_string is not None:
            search_pattern = expect_string
        else:
            search_pattern = self.prompt

        start_time = time.time()

        self.SSH_shell.send(command_string)

        while not self.SSH_shell.recv_ready():
            pass

        while time.time() - start_time <= self.timeout:

            new_data = self.SSH_shell.recv(65535).decode('utf-8')

            if "--More--" in new_data:
                self.SSH_shell.send(" ")

                while not self.SSH_shell.recv_ready():
                    pass

            data += new_data

            if len(findall("\S+\s*"+search_pattern, new_data)) > 0:
                break

            time.sleep(loop_delay)

        return data


    if False:
        pass
        def cli(self, command):
            """ Run singlecommand in Datacom paramiko connection"""

            cli_output = ""
            n = 0

            self.device.send(command)

            while not self.device.recv_ready():
                pass
            
            while n < self.timeout*2:

                cli_output += self.device.recv(65535).decode('utf-8')

                if "--More--" in cli_output:
                    self.device.send(" ")

                    while not self.device.recv_ready():
                        pass

                sleep(0.5)
                n+=1

                if len(findall("\S+\s*"+self.prompt, cli_output)) > 0:
                    break

            cli_output = sub("--More--\s*", "", cli_output)

            return cli_output

    def paramiko_cleanup(self) -> None:
        """Cleanup Paramiko to try to gracefully handle SSH session ending."""
        if self.remote_conn_pre is not None:
            self.remote_conn_pre.close()
        del self.remote_conn_pre

    def _modify_connection_params(self) -> None:
        """Modify connection parameters prior to SSH connection."""
        pass
        