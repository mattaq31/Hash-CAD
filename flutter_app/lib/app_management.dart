/// Application state management and lifecycle.
///
/// Provides state management classes including [DesignState], [ActionState],
/// and [ServerState] for managing the application's data and UI state.
library app_management;

export 'app_management/shared_app_state.dart';
export 'app_management/action_state.dart';
export 'app_management/server_state.dart';
export 'app_management/app_preferences.dart';
export 'app_management/slat_undo_stack.dart';
export 'app_management/update_state.dart';
export 'app_management/update_service.dart';
export 'app_management/version_tracker.dart';
export 'app_management/main_design_io.dart';
export 'app_management/git_version_updater.dart';
// Mixins
export 'app_management/design_state_mixins/design_state_contract.dart';
export 'app_management/design_state_mixins/design_state_core_mixin.dart';
export 'app_management/design_state_mixins/design_state_file_io_mixin.dart';
export 'app_management/design_state_mixins/design_state_layer_mixin.dart';
export 'app_management/design_state_mixins/design_state_slat_mixin.dart';
export 'app_management/design_state_mixins/design_state_handle_mixin.dart';
export 'app_management/design_state_mixins/design_state_slat_color_mixin.dart';
export 'app_management/design_state_mixins/design_state_phantom_mixin.dart';
export 'app_management/design_state_mixins/design_state_cargo_mixin.dart';
export 'app_management/design_state_mixins/design_state_seed_mixin.dart';
export 'app_management/design_state_mixins/design_state_plate_mixin.dart';
export 'app_management/design_state_mixins/design_state_handle_link_mixin.dart';
