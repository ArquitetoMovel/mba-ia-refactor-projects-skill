from middlewares.error_handler import AppError


def ensure_can_view(user_id, actor):
    if actor.id != user_id and not actor.is_admin():
        raise AppError('Acesso negado: visualize apenas os seus próprios dados', 403)


def ensure_can_modify(user_id, actor, changing_role=False):
    if changing_role and not actor.is_admin():
        raise AppError('Apenas administradores podem alterar roles', 403)
    if actor.id != user_id and not actor.is_admin():
        raise AppError('Acesso negado: edite apenas o seu próprio cadastro', 403)
