base_class = "form-control"

WEBVIRTCLOUD_CRISPY_CLASS_CONVERTERS = {
    "textinput": f"{base_class} test-class",
    "passwordinput": base_class,
    "emailinput": base_class,
    "urlinput": base_class,
    "fileinput": base_class,
    "numberinput": base_class,
    "dateinput": base_class,
    "textarea": base_class,
    "password": base_class,
    "hidden": base_class,
    "radioset": "form-check",
    "checkboxinput": "form-check-input",
    "checkboxselectmultiple": "form-check",
    "radioselect": "form-check",
    "select": "form-select",
    "selectmultiple": "form-select",
}
