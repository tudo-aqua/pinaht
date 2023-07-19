import pinaht.application as app
from pinaht.strategies.fast_strategy import FastStrategy
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.types.status import Status
from pinaht.knowledge.types.name import Name
from pinaht.knowledge.types.os import OS
from pinaht.knowledge.types.version import Version
from pinaht.knowledge.types.ipaddress import IPAddress
from pinaht.knowledge.types.operatingsystemtype import OperatingSystemType
from graphviz import Source
import pinaht.knowledge.precondition_factory.metapreconditions as meta
import pinaht.knowledge.precondition_factory.preconditions as pre


def test():
    target = Target()
    target2 = Target()

    status = Status.UP
    name = Name("User")
    v = Version()
    v.set_version(Version.parse_version("10.2"))
    ost = OperatingSystemType.LINUX
    os = OS()

    ip = IPAddress(500)
    print(f"the IP is {ip}")
    os2 = OS()
    ost2 = OperatingSystemType.WINDOWS

    a = app.Application(
        FastStrategy,
        [
            (None, "target", target),
            (target, "status", status),
            (target, "os", os),
            (target, "hostname", name),
            (os, "os_type", ost),
            (os, "expected_version", v),
            (None, "target", target2),
            (target2, "os", os2),
            (os2, "os_type", ost2),
        ],
        [],
    )

    visualization_str = a.manager.gen_visualization("./pinaht/knowledge/types/types.yaml")
    dot = Source(visualization_str)
    dot.render("Knowledge_Graph.gv")

    print("static")
    a = meta.static(["a", "b"])
    print(a.holds(**{"a": status, "b": name}))

    print("identical_parents")
    b = meta.identical_parents(["a", "b"])
    print(b.holds(**{"a": status, "b": name}))

    c = meta.identical_parents(["a", "b"])
    print(c.holds(**{"a": status, "b": v}))

    print("identical_ancestors")
    d = meta.identical_ancestors(["a", "b"])
    print(d.holds(**{"a": status, "b": v}))
    print(d.holds(**{"a": status, "b": status}))
    print(d.holds(**{"a": ost, "b": ost2}))
    print(d.holds(**{"a": ost, "b": v}))

    print("invert")
    e = meta.invert(a)
    print(e.holds(**{"a": status, "b": name}))

    print("merge")
    f = meta.merge([a, b])
    print(f.holds(**{"a": status, "b": name}))

    print("is_parent")
    g = meta.is_parent("target", ["name"])
    print(g.holds(**{"target": target, "name": name}))

    print("check str")
    precon = pre.check_str(lambda k: 1.0 if "apache" in str.lower(k) else 0.0)
    n = Name("apache httpd")
    print(precon.holds(n))
