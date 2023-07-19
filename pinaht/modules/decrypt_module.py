from pinaht.file_manager import FileManager
from pinaht.modules.module import Module
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.precondition_factory.preconditions import check_type
from pinaht.knowledge.precondition_factory.metapreconditions import is_parent
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.types.credentials import Credentials
from pinaht.knowledge.types.password import Password
from typing import Tuple, Dict
import base64
from pinaht.reporting.report_util import str_to_latex


class DecryptModule(Module):
    """
    Decrypts unmatched Passwords from BASE64
    """

    def __init__(self, manager, file_manager: FileManager, **kwargs):
        super().__init__(manager, **kwargs)

        self._file_manager = file_manager

        self.estimated_time = 0.5
        self.success_chance = 1.0

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """
        Generates the preconditions
        """
        cred_precondition = check_type(Credentials)

        class ValidBasePasswordPrecondition(Precondition):
            def __init__(self, **kwargs):
                super(ValidBasePasswordPrecondition, self).__init__(**kwargs)

            def holds(self, knowledge: Knowledge) -> float:
                if isinstance(knowledge, Password):
                    if str(knowledge) == "":
                        return 0.0
                    try:
                        base64.b64decode(knowledge, validate=True)
                    except base64.binascii.Error:
                        return 0.0
                    return 1.0
                return 0.0

            def doc(self, knowledge: Knowledge) -> str:
                return "checks if the given password is encoded in BASE64"

        return {
            "base64_password": (
                {"credentials": cred_precondition, "valid_password": ValidBasePasswordPrecondition()},
                is_parent("credentials", ["valid_password"]),
            )
        }

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        Decrypts a BASE64 encoded Password
        """
        cred = keyed_knowledge["credentials"]
        base64_password = keyed_knowledge["valid_password"]

        try:
            decoded = base64.b64decode(base64_password, validate=True)
            try:
                passw = decoded.decode("utf-8")  # TODO try other encodings
                buffered_module_manager.report(
                    f"Decodes password \\code{{{str_to_latex(base64_password)}}} \
                                                    into \\code{{{str_to_latex(passw)}}}"
                )
                buffered_module_manager.add_knowledge(cred, "passwords", Password(passw), 1.0)
            except UnicodeDecodeError:
                print(f"Das Passwort {base64_password} ist nicht Unicode encodiert!")
                return
        except base64.binascii.Error:
            print(f"Das Passwort {base64_password} ist nicht BASE64 encodiert!")
            return
