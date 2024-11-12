<%@ page import="java.io.*, java.net.*, java.util.*" %>
<%@ page language="java" contentType="application/json; charset=UTF-8" %>
<%@ page import="org.json.simple.JSONObject" %>
<%
    // 매뉴얼 웍스 외부 시스템 가져오기 테스트
    String currentUrl = request.getRequestURL().toString();

    String paramValue = request.getParameter("item");

    String newUrl = "https://raw.githubusercontent.com/TOBESOFT-DOCS/CHM_Nexacro_N_V24/refs/heads/main/docs/" + paramValue + ".json";

    try {
        URL url = new URL(newUrl);
        URLConnection conn = url.openConnection();

        BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
        StringBuilder content = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            content.append(line);
        }
        reader.close();

		out.println(content.toString());
    } catch (Exception e) {
        out.println("Error: " + e.getMessage());
    }
%>
