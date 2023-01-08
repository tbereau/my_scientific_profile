class AuthorSingleton(type):
    _instances = []

    def __call__(cls, *args, **kwargs):
        candidate_instance = super(AuthorSingleton, cls).__call__(*args, **kwargs)

        def matching_instance() -> type(cls) | None:
            for candidate_ in cls._instances:
                if candidate_instance == candidate_:
                    new_instance = candidate_.combine_with_other_author(
                        candidate_instance
                    )
                    cls._instances.remove(candidate_)
                    return new_instance
            return None

        if candidate := matching_instance():  # noqa
            instance = candidate
        else:
            instance = candidate_instance
        cls._instances.append(candidate_instance)
        return instance


class PaperSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        key = kwargs.get("doi") or args[0]
        if key in cls._instances.keys():
            return cls._instances[key]
        else:
            cls._instances[key] = super(PaperSingleton, cls).__call__(*args, **kwargs)
            return cls._instances[key]
