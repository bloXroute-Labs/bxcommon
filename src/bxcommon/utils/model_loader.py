def load(model_class, model_params):
    """
    NOTE: A similar model loader exists in BXAPI - if making changes, check both for consistency

    Ensures models are forward compatible - if attributes are added to models in future versions and these models saved
    to Redis, this function ensures that only the attributes that the current version knows about are loaded
    :param model_class: Model class to load into
    :param model_params: Attributes to create the model with
    :return: An instance of the passed in class instantiated with the given params
    """
    return model_class(**{key: model_params[key] for key in model_class().__dict__ if key in model_params})
