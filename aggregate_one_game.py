# TODO :
# 세컨 찬스에 의한 득점 계산 : 공리 후 득점?

import numpy as np
import pandas as pd


def get_percentage(sheet, stat):
    sheet = sheet.copy()
    sheet[f"{stat}성공률"] = sheet[f"{stat}성공"] * 100 / (sheet[f"{stat}성공"] + sheet[f"{stat}시도"])
    sheet[f"{stat}성공률"] = np.where(sheet[f"{stat}성공률"].isna(), 0.0, sheet[f"{stat}성공률"]).round(1).astype(str)
    sheet[f"{stat}성공률"] = (
        sheet[f"{stat}성공률"]
        + "% ("
        + sheet[f"{stat}성공"].astype(int).astype(str)
        + "/"
        + (sheet[f"{stat}성공"] + sheet[f"{stat}시도"]).astype(int).astype(str)
        + ")"
    )
    return sheet[f"{stat}성공률"]


def get_cumsum_of_player(sheet, player, start_q="1Q", start_t="10:00", end_q="4Q", end_t="00:00"):
    sheet = sheet.copy()
    sheet = sheet.query("기타파울==0 and 기타==0 and 선수==@player")
    if start_q == end_q:
        sheet = sheet.query("쿼터==@start_q and @end_t <= 시간 <= @start_t")
    else:
        sheet = sheet.query(
            "(쿼터 == @start_q and 시간 <= @start_t) or (@start_q < 쿼터 < @end_q) or (쿼터 == @end_q and 시간 >= @end_t)"
        )
    out = sheet.groupby(["팀", "선수"])[
        [
            "득점",
            "2점슛시도",
            "2점슛성공",
            "3점슛시도",
            "3점슛성공",
            "필드골시도",
            "필드골성공",
            "자유투시도",
            "자유투성공",
            "어시스트",
            "리바운드",
            "덩크",
            "스틸",
            "블록",
            "파울",
            "굿디펜스",
            "턴오버",
        ]
    ].sum()
    out["2점슛성공률"] = get_percentage(out, "2점슛")
    out["3점슛성공률"] = get_percentage(out, "3점슛")
    out["필드골성공률"] = get_percentage(out, "필드골")
    out["자유투성공률"] = get_percentage(out, "자유투")
    out = out[
        [
            "득점",
            "2점슛성공률",
            "3점슛성공률",
            "필드골성공률",
            "자유투성공률",
            "어시스트",
            "리바운드",
            "덩크",
            "스틸",
            "블록",
            "파울",
            "굿디펜스",
            "턴오버",
        ]
    ]
    float_cols = out.select_dtypes("float").columns
    out[float_cols] = out[float_cols].astype(int)
    return out


def summarize(sheet):
    sheet = sheet.copy()
    sheet = sheet.query("기타파울==0 and 기타==0")
    input_cols = [
        "득점",
        "2점슛시도",
        "2점슛성공",
        "3점슛시도",
        "3점슛성공",
        "필드골시도",
        "필드골성공",
        "자유투시도",
        "자유투성공",
        "어시스트",
        "리바운드",
        "덩크",
        "스틸",
        "블록",
        "파울",
        "굿디펜스",
        "턴오버",
    ]
    output_cols = [
        "득점",
        "2점슛성공률",
        "3점슛성공률",
        "필드골성공률",
        "자유투성공률",
        "어시스트",
        "리바운드",
        "덩크",
        "스틸",
        "블록",
        "파울",
        "굿디펜스",
        "턴오버",
    ]
    player = sheet.groupby(["쿼터", "팀", "선수"])[input_cols].sum()
    player_total = sheet.groupby(["팀", "선수"])[input_cols].sum()
    player_total["쿼터"] = "합계"
    player_total = player_total.reset_index().set_index(["쿼터", "팀", "선수"])
    player = pd.concat([player, player_total])
    player["2점슛성공률"] = get_percentage(player, "2점슛")
    player["3점슛성공률"] = get_percentage(player, "3점슛")
    player["필드골성공률"] = get_percentage(player, "필드골")
    player["자유투성공률"] = get_percentage(player, "자유투")
    player = player[output_cols]
    float_cols = player.select_dtypes("float").columns
    player[float_cols] = player[float_cols].astype(int)

    q1_score_margin = get_score_margin(sheet, "1Q")
    q2_score_margin = get_score_margin(sheet, "2Q")
    q3_score_margin = get_score_margin(sheet, "3Q")
    q4_score_margin = get_score_margin(sheet, "4Q")
    ot_score_margin = get_score_margin(sheet, "OT")
    total_score_margin = get_score_margin(sheet, "합계")
    score_margin = pd.concat(
        [q1_score_margin, q2_score_margin, q3_score_margin, q4_score_margin, ot_score_margin, total_score_margin]
    )

    q1_playing_time = get_playing_time(sheet, "1Q")
    q2_playing_time = get_playing_time(sheet, "2Q")
    q3_playing_time = get_playing_time(sheet, "3Q")
    q4_playing_time = get_playing_time(sheet, "4Q")
    ot_playing_time = get_playing_time(sheet, "OT")
    total_playing_time = get_playing_time(sheet, "합계")
    playing_time = pd.concat(
        [q1_playing_time, q2_playing_time, q3_playing_time, q4_playing_time, ot_playing_time, total_playing_time]
    )

    player = pd.concat([player, score_margin], axis=1)
    player = pd.concat([playing_time, player], axis=1)
    player = player.sort_values(["쿼터", "팀", "득점", "득점마진"], ascending=[True, True, False, False])

    team = sheet.groupby(["쿼터", "팀"])[input_cols].sum()
    team_total = sheet.groupby(["팀"])[input_cols].sum()
    team_total["쿼터"] = "합계"
    team_total = team_total.reset_index().set_index(["쿼터", "팀"])
    team = pd.concat([team, team_total])
    team["2점슛성공률"] = get_percentage(team, "2점슛")
    team["3점슛성공률"] = get_percentage(team, "3점슛")
    team["필드골성공률"] = get_percentage(team, "필드골")
    team["자유투성공률"] = get_percentage(team, "자유투")
    team = team[output_cols]
    float_cols = team.select_dtypes("float").columns
    team[float_cols] = team[float_cols].astype(int)

    return team, player


def get_score_margin(sheet, quarter):
    sheet = sheet.copy()
    if quarter == "합계":
        sheet["쿼터"] = "합계"
    else:
        sheet = sheet.query("쿼터==@quarter and 선수 != 0").copy()
    margin = sheet[["쿼터", "팀", "선수"]].drop_duplicates()
    margin["IN"] = False
    margin["득점마진"] = 0

    for i, row in sheet.iterrows():
        sub = row["교체"]
        team = row["팀"]
        player = row["선수"]
        if sub == "IN":
            margin.loc[(margin["팀"] == team) & (margin["선수"] == player), "IN"] = True
        elif sub == "OUT":
            margin.loc[(margin["팀"] == team) & (margin["선수"] == player), "IN"] = False
        else:
            margin.loc[(margin["IN"]) & (margin["팀"] == team), "득점마진"] += row["득점"]
            margin.loc[(margin["IN"]) & (margin["팀"] != team), "득점마진"] -= row["득점"]

    margin = margin.set_index(["쿼터", "팀", "선수"])
    margin = margin.sort_values(["쿼터", "팀", "선수"])
    margin = margin.drop(columns=["IN"])

    return margin


def get_playing_time(sheet, quarter):
    sheet = sheet.copy()
    if quarter == "합계":
        sheet["쿼터"] = "합계"
    else:
        sheet = sheet.query("쿼터==@quarter and 선수 != 0").copy()
    sheet["시간"] = sheet["시간"].str[:2].astype(int) * 60 + sheet["시간"].str[3:].astype(int)

    in_ = sheet.query("교체=='IN'").groupby(["쿼터", "팀", "선수"])[["시간"]].sum()
    out_ = sheet.query("교체=='OUT'").groupby(["쿼터", "팀", "선수"])[["시간"]].sum()

    playing_time = in_ - out_
    playing_time["시간"] = (playing_time["시간"] // 60).astype(str) + ":" + (playing_time["시간"] % 60).astype(str)

    return playing_time
