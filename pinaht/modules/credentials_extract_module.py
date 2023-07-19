from pinaht.file_manager import FileManager
from pinaht.modules.module import Module
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.precondition_factory.preconditions import check_type
from pinaht.knowledge.precondition_factory.metapreconditions import is_parent
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.types.credentials import Credentials
from pinaht.knowledge.types.name import Name
from pinaht.knowledge.types.password import Password
from pinaht.knowledge.types.fstree import FsTree
from typing import Tuple, Dict
from pinaht.reporting.report_util import str_to_latex

INTERESTING_FILENAMES = [
    "cred" "creds",
    "credential",
    "credentials",
    "confidential",
    "secret",
    "secrets",
    "geheim",
    "geheimnis",
    "nutzer",
    "benutzer",
    "users",
    "user",
    "admin",
    "admins",
    "administratoren",
    "pass",
    "password",
    "passwords",
    "passwort",
    "passwörter",
    "login",
    "logins",
    "anmeldungen",
    "anmeldedaten",
    "flag",
    "flags",
]

USABLE_FILE_TYPES = ["txt", "md"]

USER_INDICATORS = ["nutzer", "benutzer", "user", "admin", "administrator", "login"]

PASSWORD_INDICATORS = ["cred" "credential", "secret", "pass", "password", "passwort"]

MAX_PASSWORD_LENGTH = 64
MAX_USERNAME_LENGTH = 16


class CredentialsExtractModule(Module):
    """
    Extracts credentials from file hierarchies using a heuristic approach.
    """

    def __init__(self, manager, file_manager: FileManager, **kwargs):
        super().__init__(manager, **kwargs)

        self._file_manager = file_manager

        self.estimated_time = 30
        self.success_chance = 0.1

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """
        Generates the preconditions
        """
        target_precondition = check_type(Target)
        filesystem_precondition = check_type(FsTree)

        return {
            "walkable_directory": (
                {"target": target_precondition, "fsystem": filesystem_precondition},
                is_parent("target", ["fsystem"]),
            )
        }

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        Searches for usernames and Passwords
        """
        target = keyed_knowledge["target"]
        fsystem = keyed_knowledge["fsystem"]

        buffered_module_manager.report(
            "Starting to search for interesting files in the underlying filesystem object..."
        )

        if len(target.lookup["credentials"]) == 0:
            cred = Credentials()
            buffered_module_manager.add_knowledge(target, "credentials", cred, 1.0)
        else:
            cred = target.lookup["credentials"][0]

        list_of_files = fsystem.get_all_files()
        for file in list_of_files:
            file_lower = file.lower()
            try:
                file_identifier = file_lower.split("/")[-1]
                file_name = file_identifier.split(".")[0]
                file_suffix = file_identifier.split(".")[1]
            except IndexError:
                continue
            if file_suffix in USABLE_FILE_TYPES and file_name in INTERESTING_FILENAMES:
                file_bytes = fsystem.get_data(file)
                try:
                    file_string = file_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    buffered_module_manager.report(
                        f"The file \\code{{{str_to_latex(file)}}} cannot be decoded in UTF-8"
                    )
                    continue
                buffered_module_manager.report(f"File \\code{{{str_to_latex(file)}}} seems to be interesting")
                file_lines = file_string.split("\n")
                extracted = 0
                for line in file_lines:
                    if ":" in line:
                        splitted_line = line.split(":")
                        indicator_part = splitted_line[0].lower()
                        found = False
                        for indicator in USER_INDICATORS:
                            if (
                                indicator_part.find(indicator) != -1
                                and len(splitted_line[1]) <= MAX_USERNAME_LENGTH
                                and len(splitted_line[1].strip()) > 0
                            ):
                                name = Name(splitted_line[1].strip())
                                buffered_module_manager.report(f"New user \\code{{{str_to_latex(name)}}} found")
                                buffered_module_manager.add_knowledge(cred, "users", name, 1.0)
                                extracted += 1
                                found = True
                                break
                        for indicator in PASSWORD_INDICATORS:
                            if (
                                indicator_part.find(indicator) != -1
                                and len(splitted_line[1]) <= MAX_PASSWORD_LENGTH
                                and len(splitted_line[1].strip()) > 0
                            ):
                                password = Password(splitted_line[1].strip())
                                buffered_module_manager.report(
                                    f"New password \\code{{{str_to_latex(password)}}} found"
                                )
                                buffered_module_manager.add_knowledge(cred, "passwords", password, 1.0)
                                extracted += 1
                                found = True
                                break
                        if not found and " " not in line:
                            if MAX_PASSWORD_LENGTH >= len(line) > 0:
                                buffered_module_manager.add_knowledge(cred, "passwords", Password(line), 1.0)
                                extracted += 1
                            if MAX_USERNAME_LENGTH >= len(line) > 0:
                                buffered_module_manager.add_knowledge(cred, "users", Name(line), 1.0)
                                extracted += 1
                    else:
                        if MAX_PASSWORD_LENGTH >= len(line) > 0 and " " not in line:
                            buffered_module_manager.add_knowledge(cred, "passwords", Password(line), 1.0)
                            extracted += 1
                        if MAX_USERNAME_LENGTH >= len(line) > 0 and " " not in line:
                            buffered_module_manager.add_knowledge(cred, "users", Name(line), 1.0)
                            extracted += 1
                if extracted == 0:
                    buffered_module_manager.report(
                        "Filename was interesting, but extracted no passwords or usernames, perhaps it's empty"
                    )
                elif extracted == 1:
                    buffered_module_manager.report(
                        f"Extracted one credential from file \\code{{{str_to_latex(file)}}}"
                    )
                else:
                    buffered_module_manager.report(
                        f"Extracted several credentials from file \\code{{{str_to_latex(file)}}}"
                    )
