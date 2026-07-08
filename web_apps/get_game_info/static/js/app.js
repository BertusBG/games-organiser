function clean(v) {
    return v ? v.replace(/[^0-9.]/g, "") : "";
}

function copyTable() {
    let out = [];
    let t = document.getElementById("sheetTable");

    for (let r = 1; r < t.rows.length; r++) {
        let row = [];

        // Start at column 1 - skip game name in column 0
        for (let c = 1; c < t.rows[r].cells.length; c++) {
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

function clearGameNames() {
    let textarea = document.getElementById("game_name");
    console.log(textarea);
    textarea.value = "";
    textarea.focus();
}

function submitLookup() {
    document.getElementById("lookup-form").requestSubmit();
}

function handleGameNameKeydown(event) {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        submitLookup();
    }
}

function init() {
    const textarea = document.getElementById("game_name");

    if (textarea) {
        textarea.addEventListener("keydown", handleGameNameKeydown);
    }
}

init();
