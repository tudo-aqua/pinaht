from abc import ABC
from pinaht.knowledge.types.version import Version


class CPEComparable(ABC):
    """
    Interface to be able to be compared to the "Common Platform Enumeration(CPE)".
    """

    def __init__(
        self,
        part: str = "",
        vendor: str = "",
        product: str = "",
        version: Version = Version(""),
        update: str = "",
        edition: str = "",
        language: str = "en",
        **kwargs,
    ):
        """
        the constructor of the CPE class. See https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nistir7695.pdf
        for more info about CPE

        :param part: the part flag, must be in the enum Part ('/a' - application, '/h' - hardware, '/o' - OS)
        :param vendor: the vendor of the service
        :param product: the name of the product
        :param version: the version of the product given as string (delimiter must be '.') or List of Tuples
        :param update: further information about the version (e.g. 'beta')
        :param edition: is DEPRECATED and should only be used to make backwards compatible
        :param language: the language of the product (language of the interface).
        """

        super(CPEComparable, self).__init__(**kwargs)

        if part != "/a" and part != "/h" and part != "/o":
            raise ValueError("part must be a cpe part")
        self.part = part
        self.vendor = str.lower(vendor)
        self.product = str.lower(product)
        self.version = version
        self.update = str.lower(update)
        self.edition = str.lower(edition)
        self.language = str.lower(language)

    def equals(self, other):
        """
        compares a cpe comparable to a other cpe comparable, but does not check the version.

        :param other: the other service
        :return: True if the cpe comparable are the same, else False
        """
        return (
            isinstance(other, CPEComparable)
            and self.part == other.part
            and self.product == other.product
            and (self.vendor == other.vendor or self.vendor == "" or other.vendor == "")
        )

    def __str__(self):
        return "cpe:" + str(self.part) + ":" + self.vendor + ":" + self.product + ":" + str(self.version)

    def __eq__(self, other):

        return (
            isinstance(other, CPEComparable)
            and self.part == other.part
            and self.product == other.product
            and (self.vendor == other.vendor or self.vendor == "" or other.vendor == "")
            and self.version == other.version
        )

    def __lt__(self, other):

        return (
            isinstance(other, CPEComparable)
            and self.part == other.part
            and self.product == other.product
            and (self.vendor == other.vendor or self.vendor == "" or other.vendor == "")
            and self.version < other.version
        )

    def __gt__(self, other):

        return (
            isinstance(other, CPEComparable)
            and self.part == other.part
            and self.product == other.product
            and (self.vendor == other.vendor or self.vendor == "" or other.vendor == "")
            and self.version > other.version
        )
