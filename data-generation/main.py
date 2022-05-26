import sqlite3
from subprocess import Popen, PIPE



def read_next_from_db(db):
    cur.execute("select mzn, dzn from unrun_instances")
    return cur.fetchone()

def parse_output(output):
    pass

def run_flatzinc(mzn, dzb):
    process = Popen(["minizinc", "--solver Chuffed", os.path.join(".", mzn), os.path.join(".", dzn)], stdout=PIPE)
    (output, error) = process.communicate()
    if error:
        raise Exception()
    values = parse_output(output)
    return values


def write_output(db, mzn, values):
    # db.execute("INSERT INTO outputs VALUES (?,?,?)", [dict["id"], dict["name"], dict["dob"]])

def main_loop(db):
    try:
        next_mzn, next_dzn = read_next_from_db(db)
        values = run_flatzinc(next_mzn, next_dzn)
        write_output(db, next_mzn, values)
    except Exception as e:
        with open('errors.log', 'a') as f:
            f.write('{}\n'.format(str(e)))

if __name__ == '__main__':
    db = sqlite3.connect('output.db')
    main_loop(db)
