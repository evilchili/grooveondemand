def windowed_query(query, column, window_size):
    """"
    Break a Query into chunks on a given column.

    see: https://github.com/sqlalchemy/sqlalchemy/wiki/RangeQuery-and-WindowedRangeQuery
    """
    single_entity = query.is_single_entity
    query = query.add_columns(column).order_by(column)
    last_id = None

    while True:
        sub_query = query
        if last_id is not None:
            sub_query = sub_query.filter(column > last_id)
        chunk = sub_query.limit(window_size).all()
        if not chunk:
            break
        last_id = chunk[-1][-1]
        for row in chunk:
            yield row

