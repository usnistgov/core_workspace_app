
/**
 * AJAX call
 */
load_form_change_workspace = function() {
    $("#assign-workspace-modal").modal("show");
    var $recordRow = $(this).parent().parent();
    $('.'+functional_object+'-id').val($recordRow.attr("objectid"));

    $.ajax({
        url : changeWorkspaceUrl,
        type : "POST",
        dataType: "json",
        data : {
            document_id: getSelectedDocument()
        },
		success: function(data){
            $("#banner_errors").hide();
            $("#assign-workspace-form").html(data.form);
	    },
        error:function(data){
            $("#assign_workspace_errors").html(data.responseText);
            $("#banner_errors").show(500)
        }
    });
};

assign_workspace = function() {
var workspace_id = $( "#id_workspaces" ).val().trim();
$.ajax({
        url : assignWorkspaceUrl,
        type : "POST",
        dataType: "json",
        data : {
            workspace_id: workspace_id,
            document_id: getSelectedDocument()
        },
		success: function(data){
           location.reload();
	    },
        error:function(data){
            $("#assign_workspace_errors").html(data.responseText);
            $("#banner_errors").show(500)
        }
    });
};



$('.assign-workspace-record-btn').on('click', load_form_change_workspace);
$('#assign-workspace-yes').on('click', assign_workspace);