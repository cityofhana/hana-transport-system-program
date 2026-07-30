# -*- coding: utf-8 -*-
import os
import random
import json
import streamlit as st

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

DATA_FILE = "transit_data.json"

def save_data():
    try:
        data = {
            "transport_types": st.session_state.get("transport_types", []),
            "routes": st.session_state.get("routes", {}),
            "stations": {f"{t}|{r}": s for (t, r), s in st.session_state.get("stations", {}).items()}
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"데이터 저장 중 오류 발생: {e}")

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                st.session_state.transport_types = data.get("transport_types", [])
                st.session_state.routes = data.get("routes", {})
                
                stations_raw = data.get("stations", {})
                st.session_state.stations = {}
                for k, v in stations_raw.items():
                    if "|" in k:
                        t, r = k.split("|", 1)
                        st.session_state.stations[(t, r)] = v
        except Exception as e:
            print(f"데이터 불러오기 중 오류 발생: {e}")

def load_sample_data():
    st.session_state.transport_types = ["시내버스"]
    st.session_state.routes = {"시내버스": ["유곡01", "유곡02"]}
    
    all_stations = ["하나공원", "하나초교", "하나고교", "하나대학교", "하나공항", "하나시청"]
    transfer_station = random.choice(all_stations)
    
    remaining_stations = [s for s in all_stations if s != transfer_station]
    random.shuffle(remaining_stations)
    
    r1_stations = [remaining_stations[0], remaining_stations[1], transfer_station]
    r2_stations = [remaining_stations[2], remaining_stations[3], remaining_stations[4], transfer_station]
    
    st.session_state.stations = {
        ("시내버스", "유곡01"): r1_stations,
        ("시내버스", "유곡02"): r2_stations
    }
    save_data()

def load_step2_data():
    if "지하철" not in st.session_state.transport_types:
        st.session_state.transport_types.append("지하철")
    if "지하철" not in st.session_state.routes:
        st.session_state.routes["지하철"] = []
    for route in ["1호선", "2호선"]:
        if route not in st.session_state.routes["지하철"]:
            st.session_state.routes["지하철"].append(route)
            
    st.session_state.stations[("지하철", "1호선")] = ["하나대역", "하나중학교역", "하나시청역", "하나공항역"]
    st.session_state.stations[("지하철", "2호선")] = ["하나묘지역", "하나하나역", "하나시청역", "하나공항역"]
    save_data()

def main():
    st.set_page_config(
        page_title="하나자치시 대중교통 안내프로그램",
        page_icon="🚍",
        layout="wide"
    )

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔒 접근 제한된 프로그램입니다")
        st.info("링크를 공유받은 사용자만 이용할 수 있습니다. 접속 비밀번호를 입력해주세요.")
        
        entered_password = st.text_input("접속 비밀번호 입력", type="password")
        if st.button("확인"):
            if entered_password == "0924":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("⚠️ 비밀번호가 올바르지 않습니다.")
        return

    if "transport_types" not in st.session_state:
        st.session_state.transport_types = []
    if "routes" not in st.session_state:
        st.session_state.routes = {}
    if "stations" not in st.session_state:
        st.session_state.stations = {}
        
    if "data_loaded" not in st.session_state:
        load_data()
        st.session_state.data_loaded = True

    st.title("🚍 하나자치시 대중교통 안내프로그램")

    st.sidebar.title("메뉴 선택")
    
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    user_mode = st.sidebar.radio(
        "사용자 모드",
        ["이용자 모드 (노선도 조회)", "관리자 모드 (편집/관리)"]
    )

    if user_mode == "관리자 모드 (편집/관리)":
        if not st.session_state.admin_authenticated:
            st.subheader("🔐 관리자 모드 인증")
            st.warning("관리자 모드에 접근하려면 관리자 비밀번호를 입력해야 합니다.")
            
            admin_pwd = st.text_input("관리자 비밀번호 입력", type="password", key="admin_pwd_input")
            if st.button("관리자 로그인"):
                if admin_pwd == "1596":
                    st.session_state.admin_authenticated = True
                    st.success("관리자 인증 성공!")
                    st.rerun()
                else:
                    st.error("⚠️ 관리자 비밀번호가 올바르지 않습니다.")
            return

    if user_mode == "이용자 모드 (노선도 조회)":
        st.subheader("🎨 하나자치시 대중교통 노선도 조회")
        st.info("💡 이용자 모드에서는 등록된 대중교통 노선도와 정류장 정보를 조회할 수 있습니다.")

        if not st.session_state.transport_types or not st.session_state.stations:
            st.warning("등록된 대중교통 또는 노선 데이터가 없습니다.")
        else:
            tabs = st.tabs(st.session_state.transport_types)

            for tab, t_name in zip(tabs, st.session_state.transport_types):
                with tab:
                    st.markdown(f"### 🚇 {t_name} 노선도")
                    
                    t_routes = st.session_state.routes.get(t_name, [])
                    t_stations = {k: v for k, v in st.session_state.stations.items() if k[0] == t_name}

                    if not t_routes or not t_stations:
                        st.info(f"'{t_name}'에 등록된 노선 또는 정류장 데이터가 없습니다.")
                        continue

                    filter_option = st.radio(
                        f"[{t_name}] 조회 방식 선택",
                        ["전체 노선 보기"] + [f"'{r}' 노선만 집중 보기" for r in t_routes],
                        horizontal=True,
                        key=f"filter_{t_name}"
                    )

                    selected_focus_route = None
                    if "만 집중 보기" in filter_option:
                        selected_focus_route = filter_option.replace("'", "").replace(" 노선만 집중 보기", "")

                    with st.expander(f"📋 '{t_name}' 상세 노선 및 정류장 목록 보기"):
                        for r_name in t_routes:
                            s_list = t_stations.get((t_name, r_name), [])
                            st.markdown(f"**[{r_name}]**")
                            if s_list:
                                st.write(" ➔ ".join([f"[{i+1}] {s}" for i, s in enumerate(s_list)]))
                            else:
                                st.write("등록된 정류장이 없습니다.")

                    if not GRAPHVIZ_AVAILABLE:
                        st.error("⚠️ Graphviz 모듈이 설치되어 있지 않습니다.")
                        continue

                    try:
                        dot = graphviz.Digraph(comment=f'{t_name} Transit Map')
                        dot.attr(rankdir='LR', splines='polyline', nodesep='1.5', ranksep='1.8', dir='none')
                        # 기본 폰트를 굵은 Arial로 지정
                        dot.attr('node', fontname='Arial Bold')

                        station_to_routes = {}
                        for (tr_name, r_name), s_list in t_stations.items():
                            for s_name in s_list:
                                if s_name not in station_to_routes:
                                    station_to_routes[s_name] = set()
                                station_to_routes[s_name].add((tr_name, r_name))

                        colors = ['#0052A4', '#00A84D', '#EF7C1C', '#00A4E1', '#996CAC', '#CD7C2F', '#747F00', '#E6186C']
                        route_colors = {}
                        color_idx = 0
                        for r_name in t_routes:
                            route_colors[(t_name, r_name)] = colors[color_idx % len(colors)]
                            color_idx += 1

                        # 범례 박스 생성 (글자 크기 키우고 볼드체 적용)
                        with dot.subgraph(name=f"cluster_legend_{t_name}") as box:
                            box.attr(label="노선 정보 (선택 가능)", style='rounded,filled', color='#f8f9fa', fillcolor='#ffffff', fontname='Arial Bold', fontsize='14', fontcolor='#333333')
                            
                            prev_node = None
                            for (tr_name, r_name), color in route_colors.items():
                                box_item_id = f"legend_box_{tr_name}_{r_name}"
                                
                                box_color = color if (not selected_focus_route or selected_focus_route == r_name) else '#CCCCCC'
                                
                                box.node(
                                    box_item_id,
                                    label=f"  {r_name}  ",
                                    shape='box',
                                    style='filled',
                                    fillcolor=box_color,
                                    fontcolor='#ffffff',
                                    fontname='Arial Bold',
                                    fontsize='13',
                                    width='1.5'
                                )
                                if prev_node:
                                    box.edge(prev_node, box_item_id, style='invis')
                                prev_node = box_item_id

                        all_unique_stations = set()
                        for (tr_name, r_name), s_list in t_stations.items():
                            if selected_focus_route and r_name != selected_focus_route:
                                continue
                            for s_name in s_list:
                                all_unique_stations.add(s_name)

                        if not selected_focus_route:
                            for s_list in t_stations.values():
                                for s_name in s_list:
                                    all_unique_stations.add(s_name)

                        for s_name in all_unique_stations:
                            r_set = station_to_routes.get(s_name, set())
                            if selected_focus_route:
                                r_set = {item for item in r_set if item[1] == selected_focus_route}
                            
                            is_transfer = len(r_set) > 1
                            
                            # 정류장 이름(xlabel) 글자 크기를 키우고 진하게(볼드체) 설정
                            dot.node(
                                f"station_{t_name}_{s_name}",
                                label="",
                                shape='point',
                                width='0.18' if is_transfer else '0.08',
                                height='0.18' if is_transfer else '0.08',
                                xlabel=s_name,
                                fontname='Arial Bold',
                                fontcolor='#000000' if is_transfer else '#222222',
                                fontsize='13'
                            )

                        for (tr_name, r_name), s_list in t_stations.items():
                            if selected_focus_route and r_name != selected_focus_route:
                                continue
                                
                            r_color = route_colors.get((tr_name, r_name), '#000000')
                            
                            for i in range(len(s_list) - 1):
                                s_from = s_list[i]
                                s_to = s_list[i+1]
                                
                                dot.edge(
                                    f"station_{t_name}_{s_from}", 
                                    f"station_{t_name}_{s_to}", 
                                    color=r_color, 
                                    penwidth='5', 
                                    weight='2',
                                    dir='none'
                                )

                        st.graphviz_chart(dot, use_container_width=True)
                    except Exception as e:
                        st.error(f"노선도 시각화 중 오류가 발생했습니다: {e}")

    else:
        st.sidebar.divider()
        st.sidebar.success("✅ 관리자 모드 접속 완료")
        
        with st.sidebar.expander("🛠️ 관리자 빠른 테스트 설정"):
            if st.button("샘플 데이터 자동 생성"):
                load_sample_data()
                st.success("샘플 데이터가 생성되었습니다!")
                st.rerun()
            if st.button("단계별 맞춤 데이터 로드 (지하철 1·2호선)"):
                load_step2_data()
                st.success("지하철 1·2호선 데이터 로드 완료!")
                st.rerun()

        admin_menu = st.sidebar.radio(
            "관리 메뉴 선택", 
            ["대중교통 종류 관리", "노선 관리", "정류장 관리"]
        )

        if admin_menu == "대중교통 종류 관리":
            st.subheader("⚙️ 대중교통 종류 추가 및 삭제")

            with st.form("add_transport_form"):
                new_transport = st.text_input("추가할 대중교통 종류 입력 (예: 지하철, 시내버스 등)")
                submitted = st.form_submit_button("종류 추가")
                if submitted:
                    if new_transport.strip():
                        t_name = new_transport.strip()
                        if t_name not in st.session_state.transport_types:
                            st.session_state.transport_types.append(t_name)
                            if t_name not in st.session_state.routes:
                                st.session_state.routes[t_name] = []
                            save_data()
                            st.success(f"'{t_name}' 대중교통 종류가 추가되었습니다.")
                            st.rerun()
                        else:
                            st.warning("이미 존재하는 대중교통 종류입니다.")
                    else:
                        st.warning("대중교통 종류를 입력하세요.")

            st.divider()

            if st.session_state.transport_types:
                st.subheader("🗑️ 대중교통 종류 삭제")
                with st.form("del_transport_form"):
                    target_transport = st.selectbox("삭제할 대중교통 선택", st.session_state.transport_types)
                    del_submitted = st.form_submit_button("종류 삭제")
                    if del_submitted:
                        if target_transport in st.session_state.transport_types:
                            st.session_state.transport_types.remove(target_transport)
                            if target_transport in st.session_state.routes:
                                for r in st.session_state.routes[target_transport]:
                                    if (target_transport, r) in st.session_state.stations:
                                        del st.session_state.stations[(target_transport, r)]
                                del st.session_state.routes[target_transport]
                            save_data()
                            st.success(f"'{target_transport}' 종류와 하위 노선/정류장들이 삭제되었습니다.")
                            st.rerun()

        elif admin_menu == "노선 관리":
            st.subheader("🛤️ 대중교통별 노선 추가 및 삭제")

            if not st.session_state.transport_types:
                st.warning("등록된 대중교통 종류가 없습니다.")
            else:
                selected_transport = st.selectbox("대중교통 종류 선택", st.session_state.transport_types)

                with st.form("add_route_form"):
                    new_route = st.text_input(f"'{selected_transport}'에 추가할 노선 이름 입력")
                    route_submitted = st.form_submit_button("노선 추가")
                    if route_submitted:
                        if new_route.strip():
                            r_name = new_route.strip()
                            if selected_transport not in st.session_state.routes:
                                st.session_state.routes[selected_transport] = []
                            
                            if r_name not in st.session_state.routes[selected_transport]:
                                st.session_state.routes[selected_transport].append(r_name)
                                if (selected_transport, r_name) not in st.session_state.stations:
                                    st.session_state.stations[(selected_transport, r_name)] = []
                                save_data()
                                st.success(f"'{selected_transport}'에 '{r_name}' 노선이 추가되었습니다.")
                                st.rerun()
                            else:
                                st.warning("이미 존재하는 노선 이름입니다.")
                        else:
                            st.warning("노선 이름을 입력하세요.")

                st.divider()

                current_routes = st.session_state.routes.get(selected_transport, [])
                if current_routes:
                    st.subheader(f"🗑️ '{selected_transport}' 노선 삭제")
                    with st.form("del_route_form"):
                        target_route = st.selectbox("삭제할 노선 선택", current_routes)
                        del_route_submitted = st.form_submit_button("노선 삭제")
                        if del_route_submitted:
                            if target_route in current_routes:
                                current_routes.remove(target_route)
                                if (selected_transport, target_route) in st.session_state.stations:
                                    del st.session_state.stations[(selected_transport, target_route)]
                                save_data()
                                st.success(f"'{target_route}' 노선이 삭제되었습니다.")
                                st.rerun()
                else:
                    st.info(f"'{selected_transport}'에 등록된 노선이 없습니다.")

        elif admin_menu == "정류장 관리":
            st.subheader("🚏 노선별 정류장 추가 및 관리")

            if not st.session_state.transport_types:
                st.warning("등록된 대중교통 종류가 없습니다.")
            else:
                sel_t = st.selectbox("대중교통 종류 선택", st.session_state.transport_types, key="st_t")
                r_list = st.session_state.routes.get(sel_t, [])

                if not r_list:
                    st.warning(f"'{sel_t}'에 등록된 노선이 없습니다.")
                else:
                    sel_r = st.selectbox("노선 선택", r_list, key="st_r")
                    key_pair = (sel_t, sel_r)

                    if key_pair not in st.session_state.stations:
                        st.session_state.stations[key_pair] = []

                    current_stations = st.session_state.stations[key_pair]

                    if current_stations:
                        st.markdown(f"**현재 '{sel_r}' 노선의 정류장 순서:**")
                        st.write(" ➔ ".join([f"[{i+1}] {s}" for i, s in enumerate(current_stations)]))
                    else:
                        st.info("아직 등록된 정류장이 없습니다.")

                    with st.form("add_stations_batch_form"):
                        st.markdown("💡 **띄어쓰기로 정류장 이름을 구분하여 입력하세요.** (예: `서울역 시청 종각`)")
                        batch_input = st.text_input("추가할 정류장 일괄 입력")
                        batch_submitted = st.form_submit_button("정류장 추가")
                        if batch_submitted:
                            if batch_input.strip():
                                parsed_stations = batch_input.strip().split()
                                st.session_state.stations[key_pair].extend(parsed_stations)
                                save_data()
                                st.success(f"총 {len(parsed_stations)}개의 정류장이 추가되었습니다.")
                                st.rerun()
                            else:
                                st.warning("정류장 이름을 입력하세요.")

                    if current_stations:
                        st.divider()
                        st.subheader("✏️ 정류장 이름 변경")
                        with st.form("edit_station_form"):
                            edit_idx = st.selectbox("변경할 정류장 선택", range(len(current_stations)), format_func=lambda i: f"{i+1}. {current_stations[i]}", key="edit_idx_sel")
                            new_station_name = st.text_input("새로운 정류장 이름 입력", value=current_stations[edit_idx])
                            edit_submitted = st.form_submit_button("정류장 이름 변경")
                            if edit_submitted:
                                if new_station_name.strip():
                                    old_name = current_stations[edit_idx]
                                    changed_name = new_station_name.strip()
                                    current_stations[edit_idx] = changed_name
                                    save_data()
                                    st.success(f"정류장 이름이 '{old_name}' 에서 '{changed_name}'(으)로 변경되었습니다.")
                                    st.rerun()
                                else:
                                    st.warning("변경할 정류장 이름을 입력하세요.")

                        st.divider()
                        st.subheader("🗑️ 정류장 개별 삭제")
                        with st.form("del_station_form"):
                            target_idx = st.selectbox("삭제할 정류장 선택", range(len(current_stations)), format_func=lambda i: f"{i+1}. {current_stations[i]}")
                            del_station_submitted = st.form_submit_button("선택한 정류장 삭제")
                            if del_station_submitted:
                                removed = current_stations.pop(target_idx)
                                save_data()
                                st.success(f"'{removed}' 정류장이 삭제되었습니다.")
                                st.rerun()

if __name__ == "__main__":
    main()
