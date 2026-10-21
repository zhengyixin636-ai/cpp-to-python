// EditMetaDlg.cpp : 实现文件
//

#include "stdafx.h"
#include "EditMeta.h"
#include "EditMetaDlg.h"
#include "Util.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

#define MAXPATHSIZE 1000

// 用于应用程序“关于”菜单项的 CAboutDlg 对话框

class CAboutDlg : public CDialog
{
public:
	CAboutDlg();

// 对话框数据
	enum { IDD = IDD_ABOUTBOX };

	protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV 支持

// 实现
protected:
	DECLARE_MESSAGE_MAP()
};

CAboutDlg::CAboutDlg() : CDialog(CAboutDlg::IDD)
{

}

void CAboutDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
}

BEGIN_MESSAGE_MAP(CAboutDlg, CDialog)
END_MESSAGE_MAP()


// CEditMetaDlg 对话框




CEditMetaDlg::CEditMetaDlg(CWnd* pParent /*=NULL*/)
	: CDialog(CEditMetaDlg::IDD, pParent)
	, mXLeft(0)
	, mYButtom(0)
	, mXRight(0)
	, mYTop(0)
	, mOrginCoordXLeft(0)
	, mOrginCoordYTop(0)
	, mXCount(0)
	, mYCount(0)
	, mDEMResolution(0)
	, mDEMDestLayer(0)
	, mDEMXLeft(0)
	, mDEMYButtom(0)
	, mDEMXRight(0)
	, mDEMYTop(0)
	, mDEMCol(0)
	, mDEMRow(0)
	, mDOMResolution(0)
	, mDOMDestLayer(0)
	, mDOMXLeft(0)
	, mDOMYButtom(0)
	, mDOMXRight(0)
	, mDOMYTop(0)
	, mDOMCol(0)
	, mDOMRow(0)
{
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);
}

void CEditMetaDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	DDX_Text(pDX, IDC_XLEFT, mXLeft);
	DDX_Text(pDX, IDC_YBUTOOM, mYButtom);
	DDX_Text(pDX, IDC_XRIGHT, mXRight);
	DDX_Text(pDX, IDC_YTOP, mYTop);
	DDX_Text(pDX, IDC_XLEFT2, mOrginCoordXLeft);
	DDX_Text(pDX, IDC_YTOP2, mOrginCoordYTop);
	DDX_Text(pDX, IDC_XCOUNT, mXCount);
	DDX_Text(pDX, IDC_YCOUNT, mYCount);
	DDX_Text(pDX, IDC_RESOLUTION, mDEMResolution);
	DDX_Text(pDX, IDC_DESTLAYER, mDEMDestLayer);
	DDX_Text(pDX, IDC_XLEFT3, mDEMXLeft);
	DDX_Text(pDX, IDC_YBUTOOM2, mDEMYButtom);
	DDX_Text(pDX, IDC_XRIGHT2, mDEMXRight);
	DDX_Text(pDX, IDC_YTOP3, mDEMYTop);
	DDX_Text(pDX, IDC_COL, mDEMCol);
	DDX_Text(pDX, IDC_ROW, mDEMRow);
	DDX_Text(pDX, IDC_RESOLUTION2, mDOMResolution);
	DDX_Text(pDX, IDC_DESTLAYER2, mDOMDestLayer);
	DDX_Text(pDX, IDC_XLEFT4, mDOMXLeft);
	DDX_Text(pDX, IDC_YBUTOOM3, mDOMYButtom);
	DDX_Text(pDX, IDC_XRIGHT3, mDOMXRight);
	DDX_Text(pDX, IDC_YTOP4, mDOMYTop);
	DDX_Text(pDX, IDC_COL2, mDOMCol);
	DDX_Text(pDX, IDC_ROW2, mDOMRow);
}

BEGIN_MESSAGE_MAP(CEditMetaDlg, CDialog)
	ON_WM_SYSCOMMAND()
	ON_WM_PAINT()
	ON_WM_QUERYDRAGICON()
	//}}AFX_MSG_MAP
	ON_BN_CLICKED(IDOK, &CEditMetaDlg::OnBnClickedOk)
	ON_BN_CLICKED(IDC_EDITMETA, &CEditMetaDlg::OnBnClickedEditmeta)
	ON_BN_CLICKED(IDC_INTOMETA, &CEditMetaDlg::OnBnClickedIntometa)
	ON_WM_DESTROY()
END_MESSAGE_MAP()


// CEditMetaDlg 消息处理程序

BOOL CEditMetaDlg::OnInitDialog()
{
	CDialog::OnInitDialog();

	// 将“关于...”菜单项添加到系统菜单中。

	// IDM_ABOUTBOX 必须在系统命令范围内。
	ASSERT((IDM_ABOUTBOX & 0xFFF0) == IDM_ABOUTBOX);
	ASSERT(IDM_ABOUTBOX < 0xF000);

	CMenu* pSysMenu = GetSystemMenu(FALSE);
	if (pSysMenu != NULL)
	{
		CString strAboutMenu;
		strAboutMenu.LoadString(IDS_ABOUTBOX);
		if (!strAboutMenu.IsEmpty())
		{
			pSysMenu->AppendMenu(MF_SEPARATOR);
			pSysMenu->AppendMenu(MF_STRING, IDM_ABOUTBOX, strAboutMenu);
		}
	}

	GetDlgItem(IDC_INTOMETA)->EnableWindow(FALSE);

	// 设置此对话框的图标。当应用程序主窗口不是对话框时，框架将自动
	//  执行此操作
	SetIcon(m_hIcon, TRUE);			// 设置大图标
	SetIcon(m_hIcon, FALSE);		// 设置小图标

	// TODO: 在此添加额外的初始化代码

	return TRUE;  // 除非将焦点设置到控件，否则返回 TRUE
}

void CEditMetaDlg::OnSysCommand(UINT nID, LPARAM lParam)
{
	if ((nID & 0xFFF0) == IDM_ABOUTBOX)
	{
		CAboutDlg dlgAbout;
		dlgAbout.DoModal();
	}
	else
	{
		CDialog::OnSysCommand(nID, lParam);
	}
}

// 如果向对话框添加最小化按钮，则需要下面的代码
//  来绘制该图标。对于使用文档/视图模型的 MFC 应用程序，
//  这将由框架自动完成。

void CEditMetaDlg::OnPaint()
{
	if (IsIconic())
	{
		CPaintDC dc(this); // 用于绘制的设备上下文

		SendMessage(WM_ICONERASEBKGND, reinterpret_cast<WPARAM>(dc.GetSafeHdc()), 0);

		// 使图标在工作矩形中居中
		int cxIcon = GetSystemMetrics(SM_CXICON);
		int cyIcon = GetSystemMetrics(SM_CYICON);
		CRect rect;
		GetClientRect(&rect);
		int x = (rect.Width() - cxIcon + 1) / 2;
		int y = (rect.Height() - cyIcon + 1) / 2;

		// 绘制图标
		dc.DrawIcon(x, y, m_hIcon);
	}
	else
	{
		CDialog::OnPaint();
	}
}

//当用户拖动最小化窗口时系统调用此函数取得光标显示。
//
HCURSOR CEditMetaDlg::OnQueryDragIcon()
{
	return static_cast<HCURSOR>(m_hIcon);
}


void CEditMetaDlg::OnBnClickedOk()
{
	// TODO: 在此添加控件通知处理程序代码
	OnOK();
}


void CEditMetaDlg::WriteLog(string info)
//void CEditMetaDlg::WriteLog(char* msg)
{
	FILE* pLogFile = NULL;
	try
	{
		fopen_s(&pLogFile, m_CreateTxtfilePath.c_str(), "a");

		fprintf(pLogFile , info.c_str());
		fprintf(pLogFile ,"\n");
		//fprintf(pLogFile ,"\n");

		//fputs(msg,pLogFile);
		//fputc('\n' , pLogFile);

		fclose(pLogFile);
	}
	catch (int* e)
	{
		throw e;
	}		
}

void CEditMetaDlg::OnBnClickedEditmeta()
{
	// TODO: 在此添加控件通知处理程序代码

	string msg;
	char tempStr[64];

	TCHAR dllPath[MAXPATHSIZE];
	HMODULE dllHandle = reinterpret_cast<HMODULE>(&__ImageBase);
	GetModuleFileName(dllHandle, dllPath, MAXPATHSIZE);
	CString strDataPath = dllPath;
	int pos = strDataPath.ReverseFind('\\');
	strDataPath = strDataPath.Left(pos);
	pos = strDataPath.ReverseFind('\\');
	strDataPath = strDataPath.Left(pos);
	strDataPath += L"\\Data";

	//m_OriginMetafilePath = "D:\\HZ.meta";
	//m_CreateTxtfilePath = "D:\\HZ.txt";
	m_OriginMetafilePath = CT2A(strDataPath + L"\\HZ.meta");
	m_CreateTxtfilePath =  CT2A(strDataPath + L"\\HZ.txt");


	FILE* _file = NULL;
	FILE* _outfile = NULL;

	if (fopen_s(&_file , m_OriginMetafilePath.c_str() , "rb"))	return ;

	///工程名
	fread(&m_ProjectNameLen , sizeof(long) , 1 , _file);
	msg = Util::itos(m_ProjectNameLen);
	WriteLog(msg);

	
	fread(tempStr, m_ProjectNameLen , 1 , _file) ;
	m_projectName = tempStr;
	msg = m_projectName;
	WriteLog(msg);

	///最高层级
	fread(&m_EdLyr, sizeof(int) , 1 , _file) ;
	msg = Util::itos(m_EdLyr);
	WriteLog(msg);

	///切割范围
	fread(m_BBox, sizeof(double) * 4 , 1 , _file) ;
	for (int i=0;i<4;i++)
	{
		msg = Util::double2String(m_BBox[i]);
		WriteLog(msg);
	}

	///原点坐标信息
	fread(m_orgintCoord , sizeof(double) * 2  , 1 , _file);
	for (int i=0;i<2;i++)
	{
		msg = Util::double2String(m_orgintCoord[i]);
		WriteLog(msg);
	}

	///xBian,yBian
	fread(&m_XCount , sizeof(int) , 1 , _file) ;
	msg = Util::itos(m_XCount);
	WriteLog(msg);

	fread(&m_YCount , sizeof(int) , 1 , _file) ;
	msg = Util::itos(m_YCount);
	WriteLog(msg);

	///DEM分辨率信息
	fread(&m_DEMStructCount , sizeof(int) , 1 , _file);
	msg = Util::itos(m_DEMStructCount);
	WriteLog(msg);

	for (int i = 0; i < m_DEMStructCount ; i++)
	{
		DEMresInfo = new ResolutionInfo;
		fread(&m_DEMStructSize , sizeof(long) , 1 , _file);
		msg = Util::itos(m_DEMStructSize);
		WriteLog(msg);

		//解析分辨率相关结构体
		fread(DEMresInfo , m_DEMStructSize , 1 , _file);
		msg = Util::double2String(DEMresInfo->res);
		WriteLog(msg);

		msg = Util::itos(DEMresInfo->lyr);
		WriteLog(msg);

		for (int j=0;j<4;j++)
		{
			msg = Util::double2String(DEMresInfo->bBox[j]);
			WriteLog(msg);
		}
	
		for (int j=0;j<2;j++)
		{	
			msg = Util::itos(DEMresInfo->countSpan[j]);
			WriteLog(msg);
		}

		msg = Util::itos((int)DEMresInfo->isNeedTiler);
		WriteLog(msg);

	}

	///DOM分辨率信息
	fread(&m_DOMStructCount , sizeof(int) , 1 , _file);
	for (int i = 0; i < m_DOMStructCount ; i++)
	{
		DOMresInfo = new ResolutionInfo;
		fread(&m_DOMStructSize , sizeof(long) , 1 , _file);
		msg = Util::itos(m_DOMStructSize);
		WriteLog(msg);

		//解析分辨率相关结构体
		fread(DOMresInfo , m_DOMStructSize , 1 , _file);
		msg = Util::double2String(DOMresInfo->res);
		WriteLog(msg);

		msg = Util::itos(DOMresInfo->lyr);
		WriteLog(msg);

		for (int j=0;j<4;j++)
		{
			msg = Util::double2String(DOMresInfo->bBox[j]);
			WriteLog(msg);
		}

		for (int j=0;j<2;j++)
		{	
			msg = Util::itos(DOMresInfo->countSpan[j]);
			WriteLog(msg);
		}

		msg = Util::itos((int)DOMresInfo->isNeedTiler);
		WriteLog(msg);
	}

	if(_file)	fclose(_file);
	if(_outfile)	fclose(_outfile);


	mXLeft = m_BBox[0];
	mYButtom = m_BBox[1];
	mXRight = m_BBox[2];
	mYTop = m_BBox[3];
	mOrginCoordXLeft = m_orgintCoord[0];
	mOrginCoordYTop = m_orgintCoord[1];
	mXCount = m_XCount;
	mYCount = m_YCount;

	mDEMResolution = DEMresInfo->res;
	mDEMDestLayer = DEMresInfo->lyr;
	mDEMXLeft = DEMresInfo->bBox[0];
	mDEMYButtom = DEMresInfo->bBox[1];
	mDEMXRight = DEMresInfo->bBox[2];
	mDEMYTop = DEMresInfo->bBox[3];
	mDEMCol = DEMresInfo->countSpan[0];
	mDEMRow = DEMresInfo->countSpan[1];

	mDOMResolution = DOMresInfo->res;
	mDOMDestLayer = DOMresInfo->lyr;
	mDOMXLeft = DOMresInfo->bBox[0];
	mDOMYButtom = DOMresInfo->bBox[1];
	mDOMXRight = DOMresInfo->bBox[2];
	mDOMYTop = DOMresInfo->bBox[3];
	mDOMCol = DOMresInfo->countSpan[0];
	mDOMRow = DOMresInfo->countSpan[1];

	UpdateData(FALSE);

	GetDlgItem(IDC_EDITMETA)->EnableWindow(FALSE);
	GetDlgItem(IDC_INTOMETA)->EnableWindow(TRUE);
	return;
}

void CEditMetaDlg::OnBnClickedIntometa()
{
	// TODO: 在此添加控件通知处理程序代码


	UpdateData(TRUE);
	m_BBox[0] = mXLeft;
	m_BBox[1]=mYButtom;
	m_BBox[2]=mXRight;
	m_BBox[3]=mYTop;
	m_orgintCoord[0]=mOrginCoordXLeft;
	m_orgintCoord[1]=mOrginCoordYTop;
	m_XCount=mXCount;
	m_YCount=mYCount;

    DEMresInfo->res=mDEMResolution;
	DEMresInfo->lyr=mDEMDestLayer;
	DEMresInfo->bBox[0]=mDEMXLeft;
	DEMresInfo->bBox[1]=mDEMYButtom;
	DEMresInfo->bBox[2]=mDEMXRight;
	DEMresInfo->bBox[3]=mDEMYTop;
	DEMresInfo->countSpan[0]=mDEMCol;
	DEMresInfo->countSpan[1]=mDEMRow;

	DOMresInfo->res=mDOMResolution;
	DOMresInfo->lyr=mDOMDestLayer;
	DOMresInfo->bBox[0]=mDOMXLeft;
	DOMresInfo->bBox[1]=mDOMYButtom;
	DOMresInfo->bBox[2]=mDOMXRight;
	DOMresInfo->bBox[3]=mDOMYTop;
	DOMresInfo->countSpan[0]=mDOMCol;
	DOMresInfo->countSpan[1]=mDOMRow;


	TCHAR dllPath[MAXPATHSIZE];
	HMODULE dllHandle = reinterpret_cast<HMODULE>(&__ImageBase);
	GetModuleFileName(dllHandle, dllPath, MAXPATHSIZE);
	CString strDataPath = dllPath;
	int pos = strDataPath.ReverseFind('\\');
	strDataPath = strDataPath.Left(pos);
	pos = strDataPath.ReverseFind('\\');
	strDataPath = strDataPath.Left(pos);
	strDataPath += L"\\Data";
	//m_CreateMetafilePath =  "D:\\HZ2.meta";
	m_CreateMetafilePath = CT2A(strDataPath + L"\\HZ2.meta");

	FILE* _outfile = NULL;
	
	fopen_s(&_outfile , m_CreateMetafilePath.c_str() , "w+");
	if (!_outfile) return ;

	///工程名
	//size =strlen(m_projectName.c_str()) + 1;
	fwrite(&m_ProjectNameLen , sizeof(long) , 1 , _outfile) ;
	fwrite(m_projectName.c_str(), m_ProjectNameLen , 1 , _outfile) ;

	///最高层级
	fwrite(&m_EdLyr, sizeof(int) , 1 , _outfile) ;

	///切割范围
	fwrite(m_BBox, sizeof(double) * 4 , 1 , _outfile) ;

	///原点坐标信息
	fwrite(m_orgintCoord , sizeof(double) * 2  , 1 , _outfile);

	///xBian,yBian
	fwrite(&m_XCount, sizeof(int) , 1 , _outfile) ;
	fwrite(&m_YCount, sizeof(int) , 1 , _outfile) ;

	///DEM分辨率信息
	//m_DEMStructCount = m_projectManage->m_destDemRes.size();

	fwrite(&m_DEMStructCount , sizeof(int) , 1 , _outfile);			
	for (int i = 0; i < m_DEMStructCount ; i++)
	{
		//ResolutionInfo* resInfo = m_projectManage->m_destDemRes[i];
		//m_DEMStructSize = sizeof(*resInfo);

		fwrite(&m_DEMStructSize , sizeof(long) , 1 , _outfile);
		fwrite(DEMresInfo , m_DEMStructSize , 1 , _outfile);
	}

	///DOM分辨率信息
	//m_DOMStructCount = m_projectManage->m_destDomRes.size();
	fwrite(&m_DOMStructCount , sizeof(int) , 1 , _outfile);			
	for (int i = 0; i < m_DOMStructCount ; i++)
	{
		//ResolutionInfo* resInfo = m_projectManage->m_destDomRes[i];
		//size = sizeof(*resInfo);
		fwrite(&m_DOMStructSize , sizeof(long) , 1 , _outfile);
		fwrite(DOMresInfo , m_DOMStructSize , 1 , _outfile);
	}

	if(_outfile)	fclose(_outfile);

	GetDlgItem(IDC_INTOMETA)->EnableWindow(FALSE);
	GetDlgItem(IDC_EDITMETA)->EnableWindow(TRUE);

	if (DEMresInfo)
	{
		delete DEMresInfo;
		DEMresInfo = NULL;
	}
	if (DOMresInfo)
	{
		delete DOMresInfo;
		DOMresInfo = NULL;
	}
	return;
}

void CEditMetaDlg::OnDestroy()
{
	CDialog::OnDestroy();
	if (DEMresInfo)
	{
		delete DEMresInfo;
		DEMresInfo = NULL;
	}
	if (DOMresInfo)
	{
		delete DOMresInfo;
		DOMresInfo = NULL;
	}
	// TODO: 在此处添加消息处理程序代码
}
