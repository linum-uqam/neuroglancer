import { Viewer } from "src/neuroglancer/viewer";

import {EventActionMap} from 'neuroglancer/util/event_action_map';
import { registerActionListener } from "neuroglancer/util/event_action_map";

function makeExtraKeyBindings(keyMap: EventActionMap) {
  keyMap.set('control+keys', 'save-state');
}

function save_viewer_state(viewer : Viewer) {
  viewer.saveState();
}

export function add_custom_functionalities(viewer: Viewer) {
  makeExtraKeyBindings(viewer.inputEventMap);
  registerActionListener(viewer.element, 'save-state', () => save_viewer_state(viewer));
}
