from argostranslate import package, translate


def ensure_model_installed(from_code="de", to_code="en"):
    """
    Downloads (if needed) the Argos model for de→en
    and returns the Translation object.
    """
    package.update_package_index()
    available_packages = package.get_available_packages()
    pkg = next(
        (p for p in available_packages if p.from_code == from_code and p.to_code == to_code),
        None
    )
    if pkg is None:
        raise RuntimeError(f"No Argos model available for {from_code}→{to_code}")
    model_path = pkg.download()
    package.install_from_path(model_path)
    langs = translate.get_installed_languages()
    src = next(l for l in langs if l.code == from_code)
    dst = next(l for l in langs if l.code == to_code)
    return src.get_translation(dst)