import search_rsi as S


def specs():
    out = []
    for t in ("sma200", "sma200_rosnie", "sma50_200"):
        for m in S.MODES:
            for n, Ls in S.RSI_LEVELS.items():
                for L in Ls:
                    out.append((n, L, m, t))
            for combo in [((2, 14), (5, 35)), ((2, 14), (10, 40)), ((2, 14), (5, 40)), ((3, 14), (15, 40)), ((5, 14), (20, 40)),
                          ((2, 3, 14), (5, 15, 40))]:
                out.append((combo[0], combo[1], m, t))
    return out

S.SPECS = specs
print(len(specs()))
S.main()
