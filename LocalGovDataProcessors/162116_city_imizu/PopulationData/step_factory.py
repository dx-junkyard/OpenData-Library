class StepFactory:
    _steps = {}

    @classmethod
    def register_step(cls, step_type, step_class):
        cls._steps[step_type] = step_class

    @classmethod
    def create_step(cls, step_type, *args, **kwargs):
        step_class = cls._steps.get(step_type)
        if step_class is not None:
            return step_class(*args, **kwargs)
        else:
            raise ValueError(f"Step type {step_type} not registered")

