
t_winner_id = null;

function update_select_local_winner(t_control, t_user, t_id) {
  $(t_control).html(t_user);
  t_winner_id = t_id;
}


t_loser_id = null;

function update_select_local_loser(t_control, t_user, t_id) {
  $(t_control).html(t_user);
  t_loser_id = t_id;
}

function show_add_result_dialog() {

  d3.json("api/users", {
    method:"POST",
    body: {},
    headers: {
      "Content-type": "application/json; charset=UTF-8"
    }
  }).then( function(data_json) {

    {
      var select = document.getElementById("result_winner");
      for (val in data_json) {
        select.innerHTML += "<a class=\"dropdown-item\" href=\"#\" onclick=\"update_select_local_winner('#result_winner_btn','" + data_json[val]['username'] + "','" + data_json[val]['id'] +"')\" >" + data_json[val]['username'] + "</a>";
      }
    }
    {
      var select = document.getElementById("result_loser");
      select.innerHTML = '';
      for (val in data_json) {
        select.innerHTML += "<a class=\"dropdown-item\" href=\"#\" onclick=\"update_select_local_loser('#result_loser_btn','" + data_json[val]['username'] + "','" + data_json[val]['id'] +"')\" >" + data_json[val]['username'] + "</a>";
      }
    }

    $('#pConfirmSave').unbind();
    $('#pConfirmSave').click(function() 
    {
      if ( $("#result_winner_btn").html() == "Select" || $("#result_loser_btn").html() == "Select" ) {
        alert("Select both Winner and Loser");
        return;
      }

      if ( $("#result_winner_btn").html() == $("#result_loser_btn").html() ) {
        alert("Winner and Loser cannot be the same user.");
        return;
      }
      if ( $("#result_date").val() == "" ) {
        alert("Please select a date.");
        return;
      }

      var req = JSON.stringify({
        date: formatDate(moment($("#result_date").val(), "MM/DD/YYYY", true)), 
        winner_id: t_winner_id, 
        loser_id: t_loser_id, 
        comment: $("#result_comment").val(), 
      })

      d3.json("api/result_add", {
        method:"POST",
        body: req,
        headers: {
          "Content-type": "application/json; charset=UTF-8"
        }
      }).then( function(data_json) {
        //console.log(data_json);
        location.reload();
      });
      $('#resultModalEdit').modal('hide');
    });

    $('#resultModalEdit').modal('show'); 
  });
}

function show_delete_result_dialog(result, fn_complete) {

  $('#result_delete_detail').html(formatDateFromUTC(result.time));

  $('#pConfirmDeleteUser').unbind();
  $('#pConfirmDeleteUser').click(function() 
  {
    var req = JSON.stringify({
      id: result.id, 
    })

    d3.json("api/result_delete", {
      method:"POST",
      body: req,
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
    }).then( function(data_json) {
      if ( fn_complete ) {
        fn_complete();
      }
    });
    $('#resultDeleteModal').modal('hide');
  });

  $('#resultDeleteModal').modal('show'); 
}