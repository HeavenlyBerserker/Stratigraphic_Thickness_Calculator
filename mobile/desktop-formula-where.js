/* Formula + Where blocks mirror source/app.py (desktop QTextEdit HTML). */
globalThis.STC_FORMULA_WHERE = {
  t1:
    "<b>Formula</b><br>" +
    "T<sub>1</sub> = M(cosδ - sinδ(cos(φ<sub>d1</sub> - φ<sub>b</sub>))" +
    "tanβ<sub>1</sub>)cosβ<sub>1</sub><br><br>" +
    "<b>Where</b><br>" +
    "T<sub>1</sub>: true stratigraphic thickness<br>" +
    "M: measured thickness along the well path<br>" +
    "δ: borehole inclination from vertical down, 0° ≤ δ ≤ 180°<br>" +
    "β<sub>1</sub>: bed dip, 0° ≤ β ≤ 90°<br>" +
    "φ<sub>b</sub>, φ<sub>d1</sub>: azimuths clockwise from north, 0° ≤ φ ≤ 360°<br>" +
    "U<sub>d1</sub>: downward dip-pole unit vector<br>" +
    "U<sub>b</sub>: borehole direction unit vector",
  t2:
    "<b>Formula</b><br>" +
    "U<sub>av</sub> = (U<sub>d1</sub> + U<sub>d2</sub>) / " +
    "||U<sub>d1</sub> + U<sub>d2</sub>||<br>" +
    "T<sub>2</sub> = M (U<sub>av</sub> . U<sub>b</sub>)<br><br>" +
    "<b>Where</b><br>" +
    "T<sub>2</sub>: true stratigraphic thickness from average-vector model<br>" +
    "U<sub>d1</sub>, U<sub>d2</sub>: dip-pole unit vectors at top/base<br>" +
    "U<sub>av</sub>: normalized average dip-pole vector<br>" +
    "U<sub>b</sub>: borehole unit vector<br>" +
    "M: measured thickness along the well path",
  t3:
    "<b>Formula</b><br>" +
    "T<sub>3</sub> = (M U<sub>d1</sub> . U<sub>b</sub> + " +
    "M U<sub>d2</sub> . U<sub>b</sub>) / 2<br>" +
    "T<sub>3</sub> = M (U<sub>d1</sub> + U<sub>d2</sub>) . " +
    "U<sub>b</sub> / 2<br><br>" +
    "<b>Where</b><br>" +
    "T<sub>3</sub>: true stratigraphic thickness from average-thickness model<br>" +
    "U<sub>d1</sub>, U<sub>d2</sub>: dip-pole unit vectors at top/base<br>" +
    "U<sub>b</sub>: borehole unit vector<br>" +
    "M: measured thickness along the well path<br>" +
    ". : dot product",
  t4:
    "<b>Formula</b><br>" +
    "T<sub>4</sub> = (T<sub>2</sub> + T<sub>3</sub>) / 2<br><br>" +
    "<b>Where</b><br>" +
    "T<sub>4</sub>: mixed-average thickness (mean of T<sub>2</sub> and T<sub>3</sub>)<br>" +
    "T<sub>2</sub>: average-vector thickness<br>" +
    "T<sub>3</sub>: average-thickness value<br>" +
    "U<sub>d1</sub>, U<sub>d2</sub>, U<sub>av</sub>, U<sub>b</sub>: " +
    "supporting vectors from component models",
  t5:
    "<b>Formula</b><br>" +
    "β'<sub>2</sub> = arctan(tanβ<sub>2</sub> |cos(φ<sub>d1</sub>−φ<sub>d2</sub>)|)<br>" +
    "If smallest |φ<sub>d1</sub>−φ<sub>d2</sub>| ≤ 90°: U'<sub>d2</sub> from φ<sub>d1</sub>; " +
    "else from φ<sub>d1</sub>+180°<br>" +
    "U<sub>d1</sub> = (-cos φ<sub>d1</sub> sin β<sub>1</sub>, " +
    "-sin φ<sub>d1</sub> sin β<sub>1</sub>, cos β<sub>1</sub>)<br>" +
    "U'<sub>d2</sub> = (-cos φ<sub>eff</sub> sin β'<sub>2</sub>, " +
    "-sin φ<sub>eff</sub> sin β'<sub>2</sub>, cos β'<sub>2</sub>) " +
    "with φ<sub>eff</sub> as above<br>" +
    "N<sub>dc</sub> = (U<sub>d1</sub> x U'<sub>d2</sub>) / " +
    "||U<sub>d1</sub> x U'<sub>d2</sub>||<br>" +
    "M' = ||M<sub>b</sub> - N<sub>dc</sub>(N<sub>dc</sub> . M<sub>b</sub>)||; " +
    "M<sub>b</sub> = M U<sub>b</sub><br>" +
    "U'<sub>b</sub> = M'<sub>b</sub> / ||M'<sub>b</sub>|| with M'<sub>b</sub> = " +
    "M<sub>b</sub> - N<sub>dc</sub>(N<sub>dc</sub> . M<sub>b</sub>)<br>" +
    "U<sub>c</sub> = (U<sub>d1</sub> - U'<sub>d2</sub>) / " +
    "||U<sub>d1</sub> - U'<sub>d2</sub>||<br>" +
    "γ = arccos(U<sub>c</sub> . U'<sub>b</sub>); " +
    "η = arccos(U<sub>d1</sub> . U'<sub>d2</sub>)<br>" +
    "α = 90° − η/2; T<sub>5</sub> = M' sinγ / cos(η/2)<br><br>" +
    "<b>Where</b><br>" +
    "T<sub>5</sub>: concentric-fold thickness (Xu et al.; M' after Berg, 2011)<br>" +
    "β'<sub>2</sub>: azimuth-corrected base dip<br>" +
    "U<sub>d1</sub>, U'<sub>d2</sub>: top and corrected-base dip poles<br>" +
    "N<sub>dc</sub>: normal to dip-vector plane<br>" +
    "M<sub>b</sub>: well-path vector scaled by M; M': projected length<br>" +
    "U<sub>c</sub>: normalized (U<sub>d1</sub> − U'<sub>d2</sub>); " +
    "U'<sub>b</sub>: unit projection of M<sub>b</sub><br>" +
    "γ, η, α: γ and η from dip-pole geometry; α = 90° − η/2",
  t6:
    "<b>Formula</b><br>" +
    "N<sub>dp</sub> = (U<sub>d1</sub> x U<sub>d2</sub>) / " +
    "||U<sub>d1</sub> x U<sub>d2</sub>||<br>" +
    "M' = ||M<sub>b</sub> - N<sub>dp</sub>(N<sub>dp</sub> . M<sub>b</sub>)||; " +
    "M<sub>b</sub> = M U<sub>b</sub><br>" +
    "M'<sub>b</sub> = M<sub>b</sub> - N<sub>dp</sub>(N<sub>dp</sub> . M<sub>b</sub>); " +
    "U'<sub>b</sub> = M'<sub>b</sub> / ||M'<sub>b</sub>||<br>" +
    "U<sub>c</sub> = (U<sub>d1</sub> - U<sub>d2</sub>) / " +
    "||U<sub>d1</sub> - U<sub>d2</sub>||<br>" +
    "γ = arccos(U<sub>c</sub> . U'<sub>b</sub>)<br>" +
    "α = arccos(U<sub>d1</sub> . U<sub>c</sub>)<br>" +
    "T<sub>6</sub> = M' (sinγ / sinα)<br><br>" +
    "<b>Where</b><br>" +
    "T<sub>6</sub>: plunging-fold thickness (no base azimuth correction)<br>" +
    "U<sub>d1</sub>, U<sub>d2</sub>: top and base dip-pole vectors<br>" +
    "N<sub>dp</sub>: normal to the plane of U<sub>d1</sub> and U<sub>d2</sub><br>" +
    "M<sub>b</sub>: well-path vector scaled by M; M': projected length<br>" +
    "U<sub>c</sub>: normalized (U<sub>d1</sub> - U<sub>d2</sub>)<br>" +
    "γ: angle between U<sub>c</sub> and U'<sub>b</sub>; " +
    "α: angle between U<sub>d1</sub> and U<sub>c</sub>",
  t7:
    "<b>Formula</b><br>" +
    "N<sub>dp</sub> = (U<sub>d1</sub> x U<sub>d2</sub>) / " +
    "||U<sub>d1</sub> x U<sub>d2</sub>||<br>" +
    "M' = ||M<sub>b</sub> - N<sub>dp</sub>(N<sub>dp</sub> . M<sub>b</sub>)||; " +
    "M<sub>b</sub> = M U<sub>b</sub><br>" +
    "U'<sub>b</sub> = M'<sub>b</sub> / ||M'<sub>b</sub>|| with M'<sub>b</sub> = " +
    "M<sub>b</sub> - N<sub>dp</sub>(N<sub>dp</sub> . M<sub>b</sub>)<br>" +
    "α = arccos(U<sub>d1</sub> . U'<sub>b</sub>)<br>" +
    "η = arccos(U<sub>d1</sub> . U<sub>d2</sub>)<br>" +
    "S = N<sub>dp</sub> . U'<sub>b</sub><br>" +
    "If S &lt; 0: Top-normal = M' cos(α − η) / cos(η) &nbsp; (paper T<sub>7</sub>)<br>" +
    "If S ≥ 0: Top-normal = M' cos(α + η) / cos(η) &nbsp; (paper T<sub>7</sub>)<br>" +
    "Also Top-normal = M' (sinγ / sinμ) = M' cos(α ∓ η) / cos(η) (Berg, 2011)<br><br>" +
    "<b>Where</b><br>" +
    "T<sub>7</sub>: true stratigraphic thickness (M measured normal to the top bed; paper T<sub>7</sub>)<br>" +
    "η: angle between dip poles at top and base; S selects thickening sense<br>",
  t8:
    "<b>Formula</b><br>" +
    "Same intermediate quantities as Top-normal (N<sub>dp</sub>, M', U'<sub>b</sub>, α, η, S)<br>" +
    "Top-normal = M' cos(α ∓ η) / cos(η) per S (paper T<sub>7</sub>)<br>" +
    "T<sub>8</sub> = Top-normal × cos(η / 2) &nbsp; (equal-angle method)<br><br>" +
    "<b>Where</b><br>" +
    "T<sub>8</sub>: true stratigraphic thickness (equal-angle method; η = arccos(U<sub>d1</sub> · U<sub>d2</sub>))<br>",
};
