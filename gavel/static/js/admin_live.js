let currentAnnotators;
let currentItems;

async function refresh(token) {
    const data = await $.ajax({
        url: "/admin/live",
        type: "get",
        dataType: "json",
        error: function (error) {
            return error;
        },
        success: async function (data) {
            await data;
        }
    });
    const annotators = data.annotators;
    const counts = data.counts;
    const item_counts = data.item_counts;
    const flag_count = data.flag_count;
    const flags = data.flags;
    const item_count = data.item_count;
    const items = data.items;
    const setting_closed = data.setting_closed;
    const skipped = data.skipped;
    const votes = data.votes;
    const viewed = data.viewed;
    const sigma = data.average_sigma;
    const seen = data.average_seen;

    // Populate vote count
    let vote_count = document.getElementById("total-votes");
    vote_count.innerText = votes;

    // Populate total active projects
    let total_active = document.getElementById("total-active");
    total_active.innerText = item_count;

    // Populate avg. sigma^2
    let average_sigma = document.getElementById("average-sigma");
    average_sigma.innerText = sigma.toFixed(4);

    let average_seen = document.getElementById("average-seen");
    average_seen.innerText = seen.toFixed(2);

    // Populate reports
    let reports_table = document.getElementById("reports-body");
    reports_table.innerHTML = "";
    for (let i = 0; i < flags.length; i++) {
        const flag = flags[i];
        const annotator = await annotators[flag.annotator_id];
        const item = await items[flag.project_id];

        if (!flag.id)
            continue;

        try {

        } catch (e) {
            const reports_template = `
            <tr class="${flag.resolved ? "open" : "resolve"}">
              <td><span class="admin-check"></span></td>
              <td>'${flag.id}'</td>
              <td><a href="/admin/annotator/${annotator.id}"
                     class="colored">${annotator.name}</a></td>
              <td><a href="/admin/item/${item.id}" class="colored">${item.name}</a></td>
              <td>${item.location}</td>
              <td>${flag.reason}</td>
          <td class="compact">
            <form action="/admin/item" method="post">
              <input type="submit" name="action" value="${(item.active ? 'Disable' : 'Enable')}" class="${(item.active? 'negative': 'positive')}">
              <input type="hidden" name="item_id" value="${item.id}">
              <input type="hidden" name="_csrf_token" value="${token}">
            </form>
          </td>
              <td class="compact">
                <form action="/admin/report" method="post">
                  <input type="submit" name="action" value="${flag.resolved ? "open" : "resolve"}"
                         class="${flag.resolved ? "negative" : "positive"}">
                  <input type="hidden" name="flag_id" value="${flag.id}">
                  <input type="hidden" name="_csrf_token" value="${token}">
                </form>
              </td>
            </tr>`;


        const newRow = reports_table.insertRow(reports_table.rows.length);
        newRow.innerHTML = reports_template;

        }

    }

    // Populate projects
    let projects_table = document.getElementById("items-body");
    projects_table.innerHTML = "";
    currentItems=items;
    for (let i = 0; i < items.length; i++) {
        try {
            const item = items[i];

            if (!item.id)
                continue;

            // language=HTML
            const items_template = `
            <tr class="${(item.active ? item.prioritized ? 'prioritized' : '' : 'disabled')}">
              <td><span class="admin-check"></span></td>
              <td><a onclick="openProject(${item.id})" class="colored">${i}</a></td>
              <td>${item.name}</td>
              <td>${item.location}</td>
              <td class="preserve-formatting">${item.description}</td>
              <td>${item.mu.toFixed(4)}</td>
              <td>${item.sigma_sq.toFixed(4)}</td>
              <td>${item_counts[item.id]}</td>
              <td>${viewed[item.id]}</td>
              <td>${skipped[item.id]}</td>
              <td class="compact" data-sort="${item.prioritized}">
                <form action="/admin/item" method="post">
                  <input type="submit" name="action" value="${(item.prioritized ? 'Cancel' : 'Prioritize')}"
                         class="${(item.prioritized ? 'negative' : 'positive')}">
                  <input type="hidden" name="item_id" value="${item.id}">
                  <input type="hidden" name="_csrf_token" value="${token}">
                </form>
              </td>
              <td class="compact" data-sort="${item.active}">
                <form action="/admin/item" method="post">
                  <input type="submit" name="action" value="${(item.active ? 'Disable' : 'Enable')}"
                         class="${(item.active ? 'negative' : 'positive')}">
                  <input type="hidden" name="item_id" value="${item.id}">
                  <input type="hidden" name="_csrf_token" value="${token}">
                </form>
              </td>
              <td class="compact">
                <form action="/admin/item" method="post">
                  <input type="submit" name="action" value="Delete" class="negative">
                  <input type="hidden" name="item_id" value="${item.id}">
                  <input type="hidden" name="_csrf_token" value="${token}">
                </form>
              </td>
            </tr>`;

        const newRow = projects_table.insertRow(projects_table.rows.length);
        newRow.innerHTML = items_template;
        } catch (e) {
            console.log(e)
        }

    }

    // Populate Judges
    let judges_table = document.getElementById("judges-body");
    judges_table.innerHTML = "";
    currentAnnotators = [];

    for (let i = 0; i < annotators.length; i++) {
        try {
            const annotator = annotators[i];

            if (!annotator.id)
                continue;

            // language=HTML
            const annotator_template = `
            <tr class=${annotator.active? '' : 'disabled'}>
              <td><input type="checkbox" name="annotator" value="${annotator.id}" class="admin-check"/></td>
              <td><a onclick="openJudge(${annotator.id})" class="colored">${i}</a></td>
              <td>${annotator.name}</td>
              <td>${annotator.email}</td>
              <td>${annotator.description}</td>
              <td>${(counts[annotator.id]||0)}</td>
              <td>${(annotator.next_id||'None')}</td>
              <td>${(annotator.prev_id||'None')}</td>
              <td>${(annotator.updated || 'Undefined')}</td>
              <td class="compact">
                <form action="/admin/annotator" method="post">
                  <input type="submit" name="action" value="Email" class="neutral">
                  <input type="hidden" name="annotator_id" value="${annotator.id}">
                  <input type="hidden" name="_csrf_token" value="${token}">
                </form>
              </td>
              <td class="compact" data-sort="${annotator.active}">
                <form action="/admin/annotator" method="post">
                  <input type="submit" name="action" value="${(annotator.active ? 'Disable' : 'Enable')}"
                         class="${(annotator.active ? 'negative' : 'positive')}">
                  <input type="hidden" name="annotator_id" value="${annotator.id}">
                  <input type="hidden" name="_csrf_token" value="${token}">
                </form>
              </td>
              <td class="compact">
                <form action="/admin/annotator" method="post">
                  <input type="submit" name="action" value="Delete" class="negative">
                  <input type="hidden" name="annotator_id" value="${annotator.id}">
                  <input type="hidden" name="_csrf_token" value="${token}">
                </form>
              </td>
            </tr>`;

        const newRow = judges_table.insertRow(judges_table.rows.length);
        newRow.innerHTML = annotator_template;
        } catch (e) {
            console.log(e);
        }
    }

    $('#judges').trigger("update");
    $('#reports').trigger("update");
    $('#projects').trigger("update");
}

