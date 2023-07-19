import yaml
import os
import jinja2 as ji2
from graphviz import Source


USER_METHOD_SEPERATOR = "### USER DEFINED METHODS ###"


def check_model_consistency(model):
    if model is None:
        raise ValueError("The model is None.")
    if "types" not in model:
        raise ValueError("The model does not contain any type!")
    if "config" not in model:
        raise ValueError("No general config found.")
    if "visualization" not in model:
        raise ValueError("No style configuration found.")

    for key in ["licence_text", "import_prefix", "visualization_filename", "root_type"]:
        if key not in model["config"]:
            raise ValueError("General configuration not complete. Missing key: " + key + ".")

    for key in [
        "branch_color",
        "inter_color",
        "leaf_extends_color",
        "leaf_enum_color",
        "leaf_custom_color",
        "node_label_fontname",
        "node_label_fontsize",
        "node_label_fontcolor",
        "node_content_fontname",
        "edge_label_fontname",
        "edge_label_fontsize",
        "edge_label_fontcolor",
        "leaf_shape",
        "branch_shape",
        "inter_shape",
        "abstract_color",
        "abstract_shape",
        "edge_normal_shape",
        "edge_abstract_shape",
        "node_content_max_line_length",
    ]:
        if key not in model["visualization"]:
            raise ValueError("Visualization style configuration not complete. Missing key: " + key + ".")
        if model["visualization"][key] == "":
            raise ValueError("Visualization style configuration attribute '" + key + "' can't be empty")

    recognized_types = []
    recognized_types_kind = {}
    for classtype in model["types"]:
        if "name" not in classtype:
            raise ValueError("Missing name attribute in a type.")
        if "kind" not in classtype:
            raise ValueError("Missing 'kind' attribute in type '" + classtype["name"] + "'.")
        if "description" not in classtype:
            raise ValueError("Missing description in type '" + classtype["name"] + "'.")
        recognized_types.append(classtype["name"])
        recognized_types_kind[classtype["name"]] = classtype["kind"]

    for classtype in model["types"]:
        if "extends" in classtype:
            if classtype["extends"] == "" or " " in classtype["extends"]:
                raise ValueError("Type '" + classtype["name"] + "' can extend exactly one Type.")
            if classtype["extends"] not in recognized_types:
                raise ValueError(
                    "Type '"
                    + classtype["name"]
                    + "' extends type '"
                    + classtype["extends"]
                    + "', which is not found."
                )
            if not recognized_types_kind[classtype["extends"]] == "ABSTRACT":
                raise ValueError(
                    "Type '"
                    + classtype["name"]
                    + "' extends type '"
                    + classtype["extends"]
                    + "', which is not of kind 'ABSTRACT'."
                )
            for possible_abstract_class in model["types"]:
                if (
                    possible_abstract_class["name"] == classtype["extends"]
                    and "childs" in possible_abstract_class
                    and not classtype["kind"] == "BRANCH"
                ):
                    raise ValueError(
                        "Type '"
                        + classtype["name"]
                        + "' extends from '"
                        + possible_abstract_class["name"]
                        + "' which has defined childs, thus type '"
                        + classtype["name"]
                        + "' has to be of kind 'BRANCH'."
                    )
        if classtype["kind"] == "BRANCH":
            if "childs" not in classtype:
                if "extends" in classtype:
                    for possible_abstract_class in model["types"]:
                        if possible_abstract_class["name"] == classtype["extends"]:
                            if "childs" not in possible_abstract_class:
                                raise ValueError(
                                    "Type '"
                                    + classtype["name"]
                                    + "' extends from '"
                                    + possible_abstract_class["name"]
                                    + "' which has not defined childs, thus type '"
                                    + classtype["name"]
                                    + "' has to define childs."
                                )
                            if len(possible_abstract_class["childs"]) < 1:
                                raise ValueError(
                                    "Type '"
                                    + classtype["name"]
                                    + "' extends from '"
                                    + possible_abstract_class["name"]
                                    + "' which has not defined childs, thus type '"
                                    + classtype["name"]
                                    + "' has to define childs."
                                )
                else:
                    raise ValueError(
                        "Missing 'childs' attribute in type '" + classtype["name"] + "' and kind of 'BRANCH'."
                    )
            else:
                for childtype in classtype["childs"]:
                    if "name" not in childtype:
                        raise ValueError("Missing 'name' attribute in a child of type '" + classtype["name"] + "'.")
                    if childtype["name"] == "":
                        raise ValueError(
                            "'name' attribute in a child of type '" + classtype["name"] + "' cannot be empty."
                        )
                    if "classname" not in childtype:
                        raise ValueError(
                            "Missing 'classname' attribute in a child of type '" + classtype["name"] + "'."
                        )
                    if childtype["classname"] not in recognized_types:
                        raise ValueError(
                            "Child with classname '"
                            + childtype["classname"]
                            + "' of type '"
                            + classtype["name"]
                            + "' is not a known type."
                        )
                    if "type" not in childtype:
                        raise ValueError("Missing 'type' attribute in a child of type '" + classtype["name"] + "'.")
                    if childtype["type"] not in ["SINGLETON", "LIST"]:
                        raise ValueError(
                            "'type' attribute in a child of type '"
                            + classtype["name"]
                            + "' has to be a value of 'SINGLETON' or 'LIST'."
                        )
            if "is" in classtype:
                raise ValueError("Type '" + classtype["name"] + "' of kind 'BRANCH' can't have attribute 'is'.")
            if "enum" in classtype:
                raise ValueError("Type '" + classtype["name"] + "' of kind 'BRANCH' can't have attribute 'enum'.")
        elif classtype["kind"] == "LEAF_EXTENDS":
            if "childs" in classtype:
                raise ValueError(
                    "Type '" + classtype["name"] + "' of kind 'LEAF_EXTENDS' can't have attribute 'childs'."
                )
            if "is" not in classtype:
                raise ValueError(
                    "Missing 'is' attribute in type '" + classtype["name"] + "' and kind of 'LEAF_EXTENDS'."
                )
            if classtype["is"] == "":
                raise ValueError(
                    "'is' attribute in type '"
                    + classtype["name"]
                    + "' is empty, should be name of a python basic type."
                )
            if "enum" in classtype:
                raise ValueError(
                    "Type '" + classtype["name"] + "' of kind 'LEAF_EXTENDS' can't have attribute 'enum'."
                )
        elif classtype["kind"] == "LEAF_ENUM":
            if "childs" in classtype:
                raise ValueError(
                    "Type '" + classtype["name"] + "' of kind 'LEAF_ENUM' can't have attribute 'childs'."
                )
            if "is" in classtype:
                raise ValueError("Type '" + classtype["name"] + "' of kind 'LEAF_ENUM' can't have attribute 'is'.")
            if "enum" not in classtype:
                raise ValueError(
                    "Missing 'enum' attribute in type '" + classtype["name"] + "' and kind of 'LEAF_ENUM'."
                )
            if len(classtype["enum"]) < 1:
                raise ValueError(
                    "Type '" + classtype["name"] + "' of kind 'LEAF_ENUM' should have at least one enumeration value."
                )
            for enumval in classtype["enum"]:
                if enumval == "":
                    raise ValueError("Empty enum value in type '" + classtype["name"] + "'.")
        elif classtype["kind"] == "LEAF_CUSTOM":
            if "childs" in classtype:
                raise ValueError(
                    "Type '" + classtype["name"] + "' of kind 'LEAF_CUSTOM' can't have attribute 'childs'."
                )
            if "is" in classtype:
                raise ValueError("Type '" + classtype["name"] + "' of kind 'LEAF_CUSTOM' can't have attribute 'is'.")
            if "enum" in classtype:
                raise ValueError(
                    "Type '" + classtype["name"] + "' of kind 'LEAF_CUSTOM' can't have attribute 'enum'."
                )
        elif classtype["kind"] == "ABSTRACT":
            if "is" in classtype:
                raise ValueError("Type '" + classtype["name"] + "' of kind 'ABSTRACT' can't have attribute 'is'.")
            if "enum" in classtype:
                raise ValueError("Type '" + classtype["name"] + "' of kind 'ABSTRACT' can't have attribute 'enum'.")
            if "extends" in classtype:
                raise ValueError(
                    "Type '" + classtype["name"] + "' of kind 'ABSTRACT' can't have attribute 'extends'."
                )
        else:
            raise ValueError("Unrecognized kind '" + classtype["kind"] + "' of type '" + classtype["name"] + "'.")


def get_types_obj(filename):
    try:
        with open(filename, "r") as sfile:
            try:
                return yaml.load(sfile, Loader=yaml.FullLoader)
            except yaml.YAMLError as ex:
                print("[ERROR] Failed to parse settings file: " + str(ex))
    except Exception as ex:
        print("[ERROR] Failed to open file: " + str(ex))
        return None


def preprocess_general_info(info_obj):
    ltext = (
        ("#" * 79)
        + "\n# Generated By: generate.py\n# User: "
        + "-"  # os.environ.get("USER")
        + "\n# Date: "
        + "-"  # datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        + "\n"
    )
    if "licence_text" in info_obj["config"] and not info_obj["config"]["licence_text"] == "":
        ltext = ltext + "# Licence: " + info_obj["config"]["licence_text"] + "\n"
    ltext += "#" * 79
    obj = {"licence_text": ltext, "import_prefix": info_obj["config"]["import_prefix"]}
    return obj


def preprocess_class_info(info_obj):
    obj = {}
    for input_class in info_obj["types"]:
        imports = []
        metaclasses = []

        if "extends" in input_class and not input_class["extends"] == "":
            metaclass = input_class["extends"]
            if (info_obj["config"]["import_prefix"] + "." + metaclass.lower(), metaclass) not in imports:
                imports.append((info_obj["config"]["import_prefix"] + "." + metaclass.lower(), metaclass))
            metaclasses.append(metaclass)

            for possible_abstract_class in info_obj["types"]:
                if possible_abstract_class["name"] == input_class["extends"] and "childs" in possible_abstract_class:
                    for abstract_child in possible_abstract_class["childs"]:
                        if "childs" not in input_class:
                            input_class["childs"] = []
                        input_class["childs"].append(abstract_child)
        else:
            metaclasses.append("Knowledge")
        if input_class["kind"] == "LEAF_EXTENDS":
            metaclasses.append(input_class["is"])
        if input_class["kind"] == "LEAF_ENUM":
            metaclasses.append("Enum")

        if "childs" in input_class and not input_class["kind"] == "ABSTRACT":
            for subclass in input_class["childs"]:
                if (
                    info_obj["config"]["import_prefix"] + "." + subclass["classname"].lower(),
                    subclass["classname"],
                ) not in imports:
                    imports.append(
                        (
                            info_obj["config"]["import_prefix"] + "." + subclass["classname"].lower(),
                            subclass["classname"],
                        )
                    )

        obj[input_class["name"]] = {"imports": imports, "metaclasses": metaclasses}

    for input_class in info_obj["types"]:
        if input_class["kind"] == "ABSTRACT" and "childs" in input_class:
            input_class["childs"] = {}

    return obj


def preprocess_type_info(info_obj):
    lst = []
    for t in info_obj["types"]:
        if "fuzzy_eq" in t and not t["fuzzy_eq"] == "":
            t["fuzzy_eq"] = (" " * 8) + t["fuzzy_eq"].replace("\n", "\n" + (" " * 8))
        if "description" not in t or t["description"] == "":
            t["description"] = "TODO: add docstring"
        lst.append(t)
    return lst


def get_user_methods(filepath):
    global USER_METHOD_SEPERATOR
    if os.path.exists(filepath):
        usermethods = ""
        with open(filepath, "r") as classfile:
            userblock = False
            while True:
                line = classfile.readline()
                if line == "":
                    break
                if userblock:
                    usermethods += line
                if USER_METHOD_SEPERATOR in line:
                    userblock = True
        return usermethods
    return ""


def generate_classfiles(input_config):
    global USER_METHOD_SEPERATOR
    current_python_file_path = os.path.dirname(os.path.realpath(__file__))
    template_file = open(os.path.join(current_python_file_path, "template.jinja"), "r")
    class_template = ji2.Template(template_file.read())
    template_file.close()

    ginfo = preprocess_general_info(input_config)
    cinfo = preprocess_class_info(input_config)
    tinfo = preprocess_type_info(input_config)

    for input_class in tinfo:
        filename = input_class["name"].lower() + ".py"
        current_python_file_path = os.path.dirname(os.path.realpath(__file__))
        filepath = os.path.join(current_python_file_path, filename)
        user_defined_methods = get_user_methods(filepath)
        with open(filepath, "w") as class_output_file:
            class_str = class_template.render(
                generalinfo=ginfo, classinfo=cinfo[input_class["name"]], typeinfo=input_class
            )
            class_output_file.write(class_str)
            class_output_file.write("    " + USER_METHOD_SEPERATOR + " # noqa: E266 \n")
            class_output_file.write(user_defined_methods)


# GRAPHVIZ generation

structure = {}
node_kind = {}

# {"classname": [node_ids]}
node_lookup = {}

# {node_id: "classname"}
node_label_lookup = []

# (ID from, ID where, edge label, edge type (False=abstract or True=normal))
edges = []

edge_counter = 1


def preprocess_visualization(input_config):
    global structure, node_lookup, node_kind
    node_kind["∅"] = ("BRANCH", "")
    for input_class in input_config["types"]:
        structure[input_class["name"]] = []
        if input_class["kind"] == "BRANCH":
            for child in input_class["childs"]:
                structure[input_class["name"]].append((child["name"], child["classname"], child["type"]))
            node_kind[input_class["name"]] = ("BRANCH", "")
        elif input_class["kind"] == "LEAF_EXTENDS":
            node_kind[input_class["name"]] = ("LEAF_EXTENDS", input_class["is"])
        elif input_class["kind"] == "LEAF_CUSTOM":
            node_kind[input_class["name"]] = ("LEAF_CUSTOM", "CUSTOM")
        elif input_class["kind"] == "LEAF_ENUM":
            node_kind[input_class["name"]] = ("LEAF_ENUM", "ENUM")
        elif input_class["kind"] == "ABSTRACT":
            for extends_child in input_config["types"]:
                if "extends" in extends_child and extends_child["extends"] == input_class["name"]:
                    structure[input_class["name"]].append(("", extends_child["name"], ""))
            node_kind[input_class["name"]] = ("ABSTRACT", "ABSTRACT")
        else:
            node_kind[input_class["name"]] = ("ERR", "ERROR")

    for classtype in structure:
        node_lookup[classtype] = []


def traverse_structure(classname):
    global structure, node_lookup, node_label_lookup, edges, edge_counter
    if node_kind[classname][0] == "ABSTRACT":
        if not node_lookup[classname][0] == -1:
            edge_counter += 1
            node = edge_counter
            node_label_lookup.append((node, classname))
            for child in structure[classname]:
                edge_counter += 1
                edges.append((node, edge_counter, "", False))
                node_label_lookup.append((edge_counter, child[1]))
                node_lookup[child[1]].append(edge_counter)
                traverse_structure(child[1])
            node_lookup[classname][0] = -1
    else:
        for node in node_lookup[classname]:
            for child in structure[classname]:
                edge_counter += 1
                if child[2] == "LIST":
                    edges.append((node, edge_counter, "[" + child[0] + "]", True))
                else:
                    edges.append((node, edge_counter, child[0], True))
                node_label_lookup.append((edge_counter, child[1]))
                node_lookup[child[1]].append(edge_counter)
                traverse_structure(child[1])
        node_lookup[classname].clear()


def generate_visualization(input_config):
    global structure, node_lookup, node_label_lookup, edges, node_kind
    preprocess_visualization(input_config)
    node_label_lookup.append((0, "∅"))
    rt = input_config["config"]["root_type"]
    edges.append((0, edge_counter, "", True))
    node_label_lookup.append((edge_counter, rt))
    node_lookup[rt].append(edge_counter)
    traverse_structure(rt)

    current_python_file_path = os.path.dirname(os.path.realpath(__file__))
    template_file = open(os.path.join(current_python_file_path, "visualization_template.jinja"), "r")
    class_template = ji2.Template(template_file.read())
    template_file.close()

    viz_str = class_template.render(
        edges=edges, labels=node_label_lookup, type_models=node_kind, style=input_config["visualization"]
    )
    dot = Source(viz_str)
    cwd = os.getcwd()
    filepath = os.path.join(cwd, "reports", input_config["config"]["visualization_filename"])
    dot.render(filepath)


def call_generation():
    current_python_file_path = os.path.dirname(os.path.realpath(__file__))
    tobj = get_types_obj(os.path.join(current_python_file_path, "types.yaml"))
    check_model_consistency(tobj)
    generate_classfiles(tobj)
    generate_visualization(tobj)


if __name__ == "__main__":
    print("Using this script directly is deprecated, use 'python -m pinaht -g' instead.")
