// EditMetaDlg.h : 头文件
//

#include<string>
using std::string;

#pragma once

typedef struct  ResolutionInfo
{
	double res;					///分辨率
	int lyr;							///目标层级
	double bBox[4];				///包围盒并集
	int countSpan[2];			///行列数
	bool isNeedTiler;			///判断是否需要切割，若数据库中的分辨率不用切割
	// 		int rangeSpan[4];			///起始终止行列号
}ResolutionInfo;

// CEditMetaDlg 对话框
class CEditMetaDlg : public CDialog
{
// 构造
public:
	CEditMetaDlg(CWnd* pParent = NULL);	// 标准构造函数

// 对话框数据
	enum { IDD = IDD_EDITMETA_DIALOG };

	protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV 支持


// 实现
protected:
	HICON m_hIcon;

	// 生成的消息映射函数
	virtual BOOL OnInitDialog();
	afx_msg void OnSysCommand(UINT nID, LPARAM lParam);
	afx_msg void OnPaint();
	afx_msg HCURSOR OnQueryDragIcon();
	DECLARE_MESSAGE_MAP()
public:
	afx_msg void OnBnClickedOk();
	afx_msg void OnBnClickedEditmeta();
	void WriteLog(string info);
	//void WriteLog(char* msg);	

	string m_OriginMetafilePath;///元数据meta文件路径
	string m_CreateTxtfilePath;///输出txt文件路径
	string m_CreateMetafilePath;///输出Metat文件路径

	long m_ProjectNameLen;//工程文件名字长度
	long m_DEMStructSize;//工程文件名字长度
	long m_DOMStructSize;//工程文件名字长度
	int m_DEMStructCount,m_DOMStructCount;//DEM、DOM分辨率结构体
	string m_projectName;
	int m_EdLyr;
	double m_BBox[4];
	double m_orgintCoord[2];
	int m_XCount , m_YCount;
	ResolutionInfo* DEMresInfo;
	ResolutionInfo* DOMresInfo;
	afx_msg void OnBnClickedIntometa();
	afx_msg void OnDestroy();
	double mXLeft;
	double mYButtom;
	double mXRight;
	double mYTop;
	double mOrginCoordXLeft;
	double mOrginCoordYTop;
	int mXCount;
	int mYCount;

	double mDEMResolution;
	int mDEMDestLayer;
	double mDEMXLeft;
	double mDEMYButtom;
	double mDEMXRight;
	double mDEMYTop;
	int mDEMCol;
	int mDEMRow;

	double mDOMResolution;
	int mDOMDestLayer;
	double mDOMXLeft;
	double mDOMYButtom;
	double mDOMXRight;
	double mDOMYTop;
	int mDOMCol;
	int mDOMRow;
};
