async function refresh(token) {
    const data = await $.ajax({
        url: "/admin/live",
        type: "get",
        dataType: "json",
        error: function (error) {
            return error;
        },
        success: async function (data) {
            return data;
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
    average_seen.innerText = seen;

    // Populate reports
    let reports_table = document.getElementById("reports-body");
    reports_table.innerHTML = "";
    for (let i = 0; i < flags.length; i++) {
        const flag = flags[i];
        const annotator = await annotators[flag.annotator_id];
        const item = await items[flag.project_id];

        if (!flag.id)
            continue;
        const resolved = flag.resolved ? "open" : "resolve";
        const resolved2 = flag.resolved ? "negative" : "positive";
        const resolved3 = flag.resolved ? "open" : "resolve";

        const reports_template = '<tr class="' + resolved + '">\n' +
            '              <td><span class="admin-check"></span></td>\n' +
            '              <td>' + flag.id + '</td>\n' +
            '              <td><a href="/admin/annotator/'+annotator.id+'"\n' +
            '                     class="colored">'+annotator.name+'</a></td>\n' +
            '              <td><a href="/admin/item/'+item.id+'" class="colored">' + item.name + '</a></td>\n' +
            '              <td>' + item.location + '</td>\n' +
            '              <td>' + flag.reason + '</td>\n' +
            '          <td class="compact">\n' +
            '            <form action="/admin/item" method="post">\n' +
            '              <input type="submit" name="action" value="'+(item.active ? 'Disable' : 'Enable')+'" class="'+(item.active? 'negative': 'positive')+'">\n' +
            '              <input type="hidden" name="item_id" value="'+item.id+'">\n' +
            '              <input type="hidden" name="_csrf_token" value="'+token+'">\n' +
            '            </form>\n' +
            '          </td> \n' +
            '              <td class="compact">\n' +
            '                <form action="/admin/report" method="post">\n' +
            '                  <input type="submit" name="action" value="' + resolved3 + '"\n' +
            '                         class="' + resolved2 + '">\n' +
            '                  <input type="hidden" name="flag_id" value="' + flag.id + '">\n' +
            '                  <input type="hidden" name="_csrf_token" value="' + token + '">\n' +
            '                </form>\n' +
            '              </td>\n' +
            '            </tr>';


        const newRow = reports_table.insertRow(reports_table.rows.length);
        newRow.innerHTML = reports_template;

    }

    // Populate projects
    let projects_table = document.getElementById("items-body");
    projects_table.innerHTML = "";
    for (let i = 0; i < items.length; i++) {
        const item = items[i];

        if (!item.id)
            continue;


        const items_template = '<tr class="' + (item.active ? item.prioritized ? 'prioritized' : '' : 'disabled') + '">\n' +
            '              <td><span class="admin-check"></span></td>\n' +
            '              <td><a href="/admin/item/'+item.id+'" class="colored">' + item.id + '</a></td>\n' +
            '              <td>' + item.name + '</td>\n' +
            '              <td>' + item.location + '</td>\n' +
            '              <td class="preserve-formatting">' + item.description + '</td>\n' +
            '              <td>' + item.mu.toFixed(4) + '</td>\n' +
            '              <td>' + item.sigma_sq.toFixed(4) + '</td>\n' +
            '              <td>' + item_counts[item.id] + '</td>\n' +
            '              <td>' + viewed[item.id] + '</td>\n' +
            '              <td>' + skipped[item.id] + '</td>\n' +
            '              <td class="compact" data-sort="' + item.prioritized + '">\n' +
            '                <form action="/admin/item" method="post">\n' +
            '                  <input type="submit" name="action" value="' + (item.prioritized ? 'Cancel' : 'Prioritize') + '"\n' +
            '                         class="' + (item.prioritized ? 'negative' : 'positive') + '">\n' +
            '                  <input type="hidden" name="item_id" value="' + item.id + '">\n' +
            '                  <input type="hidden" name="_csrf_token" value="' + token + '">\n' +
            '                </form>\n' +
            '              </td>\n' +
            '              <td class="compact" data-sort="' + item.active + '">\n' +
            '                <form action="/admin/item" method="post">\n' +
            '                  <input type="submit" name="action" value="' + (item.active ? 'Disable' : 'Enable') + '"\n' +
            '                         class="' + (item.active ? 'negative' : 'positive') + '">\n' +
            '                  <input type="hidden" name="item_id" value="' + item.id + '">\n' +
            '                  <input type="hidden" name="_csrf_token" value="' + token + '">\n' +
            '                </form>\n' +
            '              </td>\n' +
            '              <td class="compact">\n' +
            '                <form action="/admin/item" method="post">\n' +
            '                  <input type="submit" name="action" value="Delete" class="negative">\n' +
            '                  <input type="hidden" name="item_id" value="' + item.id + '">\n' +
            '                  <input type="hidden" name="_csrf_token" value="' + token + '">\n' +
            '                </form>\n' +
            '              </td>\n' +
            '            </tr>';

        const newRow = projects_table.insertRow(projects_table.rows.length);
        newRow.innerHTML = items_template;

    }

    // Populate Judges
    let judges_table = document.getElementById("judges-body");
    judges_table.innerHTML = "";
    for (let i = 0; i < annotators.length; i++) {
        const annotator = annotators[i];

        if (!annotator.id)
            continue;

        const annotator_template = '<tr class="' + (annotator.active ? '' : 'disabled') + '">\n' +
            '              <td><span class="admin-check"></span></td>\n' +
            '              <td><a href="/admin/annotator/'+annotator.id+'"\n' +
            '                     class="colored">'+annotator.id+'</a></td>\n' +
            '              <td>' + annotator.name + '</td>\n' +
            '              <td>' + annotator.email + '</td>\n' +
            '              <td>' + annotator.description + '</td>\n' +
            '              <td>' + (counts[annotator.id]||0) + '</td>\n' +
            '              <td data-sort="{{ annotator.next_id or -1 }}">' + (annotator.next_id||'None') + '</td>\n' +
            '              <td data-sort="{{ annotator.prev_id or -1 }}">' + (annotator.prev_id||'None') + '</td>\n' +
            '              <td\n' +
            '                data-sort="{{ annotator.updated | utcdatetime_epoch }}">' + (annotator.updated || 'Undefined') + '</td>\n' +
            '              <td class="compact">\n' +
            '                <form action="/admin/annotator" method="post">\n' +
            '                  <input type="submit" name="action" value="Email" class="neutral">\n' +
            '                  <input type="hidden" name="annotator_id" value="' + annotator.id + '">\n' +
            '                  <input type="hidden" name="_csrf_token" value="' + token + '">\n' +
            '                </form>\n' +
            '              </td>\n' +
            '              <td class="compact" data-sort="' + annotator.active + '">\n' +
            '                <form action="/admin/annotator" method="post">\n' +
            '                  <input type="submit" name="action" value="' + (annotator.active ? 'Disable' : 'Enable') + '"\n' +
            '                         class="' + (annotator.active ? 'negative' : 'positive') + '">\n' +
            '                  <input type="hidden" name="annotator_id" value="' + annotator.id + '">\n' +
            '                  <input type="hidden" name="_csrf_token" value="' + token + '">\n' +
            '                </form>\n' +
            '              </td>\n' +
            '              <td class="compact">\n' +
            '                <form action="/admin/annotator" method="post">\n' +
            '                  <input type="submit" name="action" value="Delete" class="negative">\n' +
            '                  <input type="hidden" name="annotator_id" value="' + annotator.id + '">\n' +
            '                  <input type="hidden" name="_csrf_token" value="' + token + '">\n' +
            '                </form>\n' +
            '              </td>\n' +
            '            </tr>';

        const newRow = judges_table.insertRow(judges_table.rows.length);
        newRow.innerHTML = annotator_template;
    }

    $('#judges').trigger("update");
    $('#reports').trigger("update");
    $('#projects').trigger("update");
}

