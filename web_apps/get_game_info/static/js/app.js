function clean(v) {
    return v ? v.replace(/[^0-9.]/g, "") : "";
}

function copyTable() {
    let out = [];
    let t = document.getElementById("sheetTable");

    for (let r = 1; r < t.rows.length; r++) {
        let row = [];

        for (let c = 0; c < t.rows[r].cells.length; c++) {
            row.push(clean(t.rows[r].cells[c].innerText.trim()));
        }

        out.push(row.join("\t"));
    }

    navigator.clipboard.writeText(out.join("\n"));
}

function copyRequirements() {
    navigator.clipboard.writeText(
        document.getElementById("reqText").innerText
    );
}
