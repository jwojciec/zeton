from datetime import datetime, timedelta

from flask import g


def parse_iso_timestamp(timestamp):
    return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")


def get_points(user_id):
    query = 'select points from users where id = ?'
    result = g.db.cursor().execute(query, [user_id])
    row = result.fetchone()
    if row:
        return row['points']
    return None


def get_weekly_highscore(user_id):
    query = 'select school_weekly_highscore from users where id = ?'
    result = g.db.cursor().execute(query, [user_id])
    row = result.fetchone()
    if row:
        return row['school_weekly_highscore']
    return None


def add_points(user_id, points):
    query = 'UPDATE users SET points = points + ? WHERE id = ?;'
    g.db.cursor().execute(query, [points, user_id])
    g.db.commit()


def get_user_data(user_id):
    query = 'select * from users where id = ?'
    result = g.db.cursor().execute(query, (user_id,))
    row = result.fetchone()
    if row:
        return dict(row)
    return None


def _add_ban_data(children):
    new_children = []
    for child in children:
        child = dict(child)
        ban_data = get_last_active_ban(child['id'])
        if ban_data:
            child['ban'] = ban_data
        new_children.append(child)
    return new_children


def get_caregivers_children(user_id):
    query = """
    SELECT u.* 
    FROM caregiver_to_child AS ctc 
    JOIN users AS u on ctc.child_id = u.id
    WHERE ctc.caregiver_id = ?
    AND u.role = 'child'
    """
    result = g.db.cursor().execute(query, (user_id,))
    children = result.fetchall()
    # to powinno być też rozwiązane po stronie bazy danych
    children = _add_ban_data(children)
    return children


def get_child_data(child_id):
    query = """
    SELECT u.* 
    FROM caregiver_to_child AS ctc 
    JOIN users AS u on ctc.child_id = u.id
    WHERE ctc.child_id = ?
    AND u.role = 'child'
    """
    result = g.db.cursor().execute(query, (child_id,))
    child = dict(result.fetchone())
    child['ban'] = get_last_active_ban(child_id)
    return child


def get_last_active_ban(user_id):
    all_bans = get_all_bans(user_id)
    # sqlite3 nie wspiera typu datetime, więc obliczenia trzeba zrobić samemu
    for ban_id, _, start, end in reversed(all_bans):
        start = parse_iso_timestamp(start)
        end = parse_iso_timestamp(end)

        if start < datetime.now() < end:
            return {'ban_id': ban_id, 'start': start, 'end': end}


def get_all_bans(user_id):
    query = 'select * from bans where user_id = ?'
    result = g.db.cursor().execute(query, [user_id])
    return result.fetchall()


def give_ban(user_id, duration_minutes):
    start = datetime.now()
    end = start + timedelta(minutes=duration_minutes)
    start_timestamp = start.isoformat()
    end_timestamp = end.isoformat()

    query = 'insert into bans values (NULL, ?, ?, ?)'
    params = (user_id, start_timestamp, end_timestamp)
    result = g.db.cursor().execute(query, params)
    g.db.commit()


def is_child_under_caregiver(child_id, caregiver_id):
    query = "SELECT * FROM caregiver_to_child WHERE child_id = ? AND caregiver_id = ?"
    result = g.db.cursor().execute(query, (child_id, caregiver_id))
    return result.fetchone()