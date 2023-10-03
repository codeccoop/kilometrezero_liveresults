import json
from sys import argv
import re


def read_file(filepath, race_id):
    file = None
    try:
        file = json.load(open(filepath, encoding="UTF-8"))
        # print('file is in unicode charset')
    except UnicodeError as unicode_error:
        try:
            file = json.load(open(filepath, encoding="Latin-1"))
            # print('file is in latin1 charset')
        except ValueError as latin_error:
            try:
                file = json.load(open(filepath, encoding="CP1252"))
                # print('file is in CP1252 charset')
            except:
                raise Exception("File encoding charset unknown. Can't read the file")

    data = file["clasificacion"]
    raw_headers = data["colnames"]
    partial_times = [
        header for header in raw_headers if "T.Int" in header or "Pos.Int" in header
    ]
    headers = (
        [
            "dorsal",
            "name",
            "generalPosition",
            "category",
            "categoryPosition",
            "time",
            "state",
        ]
        + partial_times
        + ["agrupation"]
    )

    rows = data["datos"]

    for_send = list()
    for row in rows:
        formatted_state = format_state(row[headers.index("state")], len(partial_times))
        if not formatted_state:
            continue
        else:
            row[headers.index("state")] = formatted_state

        new_row = dict()
        for i in range(len(headers)):
            new_row[headers[i]] = row[i]

        new_row["raceId"] = int(race_id)
        new_row["public"] = True

        new_row = format_int_values(new_row)

        for_send.append(new_row)

    return for_send


def format_int_values(row):
    new_row = dict()
    new_row["intPos"] = dict()
    new_row["intTime"] = dict()

    for column in row.keys():
        if "T.Int" in column:
            new_row["intTime"][column] = row[column]
        elif "Pos.Int" in column:
            new_row["intPos"][column] = row[column]
        else:
            new_row[column] = row[column]

    return new_row


def format_state(state, got_intermedium):
    state = state or "running"
    is_valid = re.findall(
        r"(finalizado|abandonado|abandono|no\s*empezado|running|descalificado|no\s*?terminado)",
        state.lower(),
    )
    if bool(is_valid):
        state = is_valid.pop()
        if (
            not re.search(
                r"(no\s*empezado|no\s*finalizado|no\s*abandono|no\s*abandonado)", state
            )
            or got_intermedium
        ):
            state = re.sub(r"no\s*", "No ", state)
            return state.capitalize()

    return False


if __name__ == "__main__":
    filepath = argv[1]
    output_path = argv[2]
    result = read_file(filepath, 54)
    with open(output_path, "w") as out:
        out.write(json.dumps(result))
