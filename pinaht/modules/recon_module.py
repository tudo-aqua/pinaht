from typing import Dict, Tuple

from pinaht.knowledge.precondition_factory.metapreconditions import is_parent
from pinaht.knowledge.types.shell import Shell
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.precondition_factory.preconditions import check_type
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.modules.module import Module
from pinaht.knowledge.types.fstree import File
from pinaht.knowledge.types.localfstree import LocalFsTree


class ReconModule(Module):
    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:

        target_precondition = check_type(Target)
        shell_precondition = check_type(Shell)

        return {
            "recon_meta": (
                {"target": target_precondition, "shell": shell_precondition},
                is_parent("target", ["shell"]),
            )
        }

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        if meta_key == "recon_meta":
            self.execute_recon(buffered_module_manager, **keyed_knowledge)

    def execute_recon(self, buffered_module_manager: BufferedModuleManager, target, shell):
        filesystem = traverse_filesystem(shell)
        fs_tree = LocalFsTree(filesystem, shell)
        buffered_module_manager.add_knowledge(target, "filesystem", fs_tree, 1.0)


def traverse_filesystem(shell):
    cmd = "find / -printf %p\\\\t%u\\\\t%g\\\\t%M\\\\n 2>/dev/null"
    fs = shell.execute(cmd)
    root = File("", "", "")

    for file in fs:
        file_info = file.rstrip("\n").split("\t")
        name = file_info[0]
        owner = file_info[1]
        group = file_info[2]
        access_rights = file_info[3]

        if name == "/":
            root.owner = owner
            root.group = group
            root.access_rights = access_rights
        else:
            root.insert(name.lstrip("/"), owner, group, access_rights)

    return root
