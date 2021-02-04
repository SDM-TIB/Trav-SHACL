class EvalPath:
    def __init__(self, shape=None, path=None):
        self.shapes = [] if shape is not None else []  # *** fix
        '''shapes = Stream.concat(
                path.getShapeStream(),
                Stream.of(shape)
        ).collect(ImmutableCollectors.toList());'''