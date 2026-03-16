from pathlib import Path

import cv2
import cv2.aruco as aruco
import numpy as np


MM_PER_INCH = 25.4


def mm_to_px(mm, dpi):
	return int(round((mm / MM_PER_INCH) * dpi))


def generate_charuco_board(
	output_path=Path("charuco_board_a4.png"),
	dpi=300,
	page_w_mm=210,
	page_h_mm=297,
	squares_x=5,
	squares_y=7,
	square_length_mm=30,
	marker_length_mm=22,
	margin_mm=10,
	dictionary_id=aruco.DICT_4X4_50,
):
	if marker_length_mm >= square_length_mm:
		raise ValueError("marker_length_mm must be smaller than square_length_mm")

	dictionary = aruco.getPredefinedDictionary(dictionary_id)

	# Metric values are used during calibration, keep these in sync with calibration code.
	board = aruco.CharucoBoard(
		(squares_x, squares_y),
		square_length_mm / 1000.0,
		marker_length_mm / 1000.0,
		dictionary,
	)

	page_w_px = mm_to_px(page_w_mm, dpi)
	page_h_px = mm_to_px(page_h_mm, dpi)
	margin_px = mm_to_px(margin_mm, dpi)

	board_w_px = mm_to_px(squares_x * square_length_mm, dpi)
	board_h_px = mm_to_px(squares_y * square_length_mm, dpi)

	if board_w_px + 2 * margin_px > page_w_px or board_h_px + 2 * margin_px > page_h_px:
		raise ValueError(
			"Board does not fit on page with requested margins. "
			"Reduce square_length_mm, squares_x/squares_y, or margin_mm."
		)

	board_img = board.generateImage((board_w_px, board_h_px), marginSize=0, borderBits=1)

	page = np.full((page_h_px, page_w_px), 255, dtype=np.uint8)
	x0 = (page_w_px - board_w_px) // 2
	y0 = (page_h_px - board_h_px) // 2
	page[y0 : y0 + board_h_px, x0 : x0 + board_w_px] = board_img

	output_path = Path(output_path)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	cv2.imwrite(str(output_path), page)

	print(f"Saved: {output_path}")
	print(f"Page: {page_w_mm}mm x {page_h_mm}mm ({page_w_px}x{page_h_px}px @ {dpi} DPI)")
	print(f"Board: {squares_x}x{squares_y} squares")
	print(f"Square length: {square_length_mm} mm")
	print(f"Marker length: {marker_length_mm} mm")
	print(f"Dictionary: DICT_4X4_50")
	print("Use these metric values in calibration:")
	print(f"  square_length = {square_length_mm / 1000.0:.6f}  # meters")
	print(f"  marker_length = {marker_length_mm / 1000.0:.6f}  # meters")


if __name__ == "__main__":
	generate_charuco_board()