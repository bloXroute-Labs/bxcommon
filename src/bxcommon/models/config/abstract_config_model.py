class AbstractConfigModel:
    def merge(self, config: "AbstractConfigModel"):
        for key, value in self.__dict__.items():
            updated_attr = getattr(config, key, None)
            if updated_attr:
                if isinstance(updated_attr, dict) and hasattr(value, "__dict__"):
                    value.__dict__.update(updated_attr)
                else:
                    self.__dict__[key] = updated_attr
        return self
