import logging
from pinaht.modules.module import Module
from abc import abstractmethod
from metasploit.msfrpc import MsfRpcClient
import subprocess


class MetasploitModule(Module):
    def __init__(self, knowledge_base, managers):
        super(MetasploitModule, self).__init__(knowledge_base, managers)

    def execute_exploit(self, exploit_name, exploit_options, payload):
        """ "
        starts Metasploit and executes the given Exploit.

        :param exploit_name: the name of the exploit
        :param exploit_options: a dictionary of options the given exploit requires
        :param payload: the payload for the exploit, can be None
        :returns tuple(hasExploitWorked, results)
            WHERE
            boolean hasExploitWorked describes weather the exploit has worked or not
            Dictionary results contains all the results of the exploit
        """
        logging.debug(
            "Inside the function execute_exploit with the name %s, the options %s and the payload %s",
            exploit_name,
            exploit_options,
            payload,
        )
        subprocess.run(["msfrpcd", "-P", "mypassword", "-n", "-f", "-a", "127.0.0.1"])
        client = MsfRpcClient("mypassword")
        exploit = client.modules.use("exploit", exploit_name)

        if self.is_exploit_options_right(exploit_options, exploit.required):
            for key, value in exploit_options.items():
                exploit[key] = value
        else:
            logging.warning("The options given for the exploit didn't meet the options required")
            return False, None

        if payload is not None:
            exploit_payload = payload
        else:
            exploit_payload = exploit.payloads[0]

        logging.debug("start execution of exploit %s", exploit_name)
        exploit_result = exploit.execute(payload=exploit_payload)
        logging.debug("end execution of exploit %s", exploit_name)

        # if the job_id is None, the exploit hasn't worked
        if exploit_result.get("job_id") is not None:
            logging.info("The exploit %s was successful", exploit_name)
            return True, client.sessions.list
        else:
            logging.warning("The execution of the exploit %s failed", exploit_name)
            return False, None

    @abstractmethod
    def check_precondition(self) -> bool:
        """
        checks the precondition of the module and returns if it can be executed

        :param knowledge_base: this is current the knowledge_base
        :returns: a boolean. True if module is executable
        """
        raise NotImplementedError()

    @abstractmethod
    def execute(self):
        """
        executes the module
        """
        raise NotImplementedError()

    @abstractmethod
    def apply_knowledge(self):
        """
        adds the knowledge to the KB
        """
        raise NotImplementedError()

    @abstractmethod
    def log_stuff(self):
        """
        logs the module
        """
        raise NotImplementedError()

    @staticmethod
    def is_exploit_options_right(options, required):
        if len(options) is len(required):
            for key in required:
                if key in options:
                    logging.debug("%s is in Required and Options")
                    pass
                else:
                    logging.debug("%s is not in required")
                    return False
        else:
            logging.debug("The lengths of options and the requirements are not the same")
            return False
