HYPOTHESIS = """W sesji europejskiej, od wtorku do czwartku, wyjście stochastyka ze strefy skrajnej
zapowiada krótkie odbicie."""

PARAMS = {"zone": [20, 15]}


def signals(df, p, ind):
    st = ind.stoch(df, 14, 3, 3)
    ok_time = (ind.session(df) == "europa") & ind.weekday(df).between(1, 3)
    long_ = ind.cross_above(st.k, p["zone"]) & ok_time
    short = ind.cross_below(st.k, 100 - p["zone"]) & ok_time
    return long_.astype("int8") - short.astype("int8")
