from pinaht.modules.heartbleed_module import HeartbleedModule
from pinaht.modules.nmap_module import NmapModule
from pinaht.modules.recon_module import ReconModule
from pinaht.modules.ssh_to_shell import SSHToShell
from pinaht.modules.apache_openfuck_module import ApacheOpenfuckModule
from pinaht.modules.ptrace_kmod_module import PtraceKmodModule
from pinaht.modules.selfscan_module import SelfScanModule
from pinaht.modules.apache_userdir_module import ApacheUserdirModule
from pinaht.modules.decrypt_module import DecryptModule
from pinaht.modules.webserver_files_module import WebserverFilesModule
from pinaht.modules.credentials_extract_module import CredentialsExtractModule
from pinaht.modules.recon_local_service import ReconLocalService
from pinaht.modules.exim4_rotw_module import Exim4ROTW
from pinaht.modules.apache_magica_module import ApacheMagicaModule
from pinaht.modules.dirty_cow_module import DirtyCowModule

extended_modules = [
    NmapModule,
    ApacheOpenfuckModule,
    PtraceKmodModule,
    SSHToShell,
    HeartbleedModule,
    SelfScanModule,
    ReconModule,
    WebserverFilesModule,
    CredentialsExtractModule,
    Exim4ROTW,
    ReconLocalService,
]
modules = [
    SelfScanModule,
    ApacheOpenfuckModule,
    PtraceKmodModule,
    SSHToShell,
    ApacheUserdirModule,
    DecryptModule,
    # ReconModule,
    WebserverFilesModule,
    CredentialsExtractModule,
    Exim4ROTW,
    ReconLocalService,
    NmapModule,
    HeartbleedModule,
    ApacheMagicaModule,
    DirtyCowModule,
]
